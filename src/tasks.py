import os
import re
import requests
import sys
import shutil
import subprocess
import time
import threading

from datetime import datetime
from multiprocessing import Lock
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from rq import get_current_job, timeouts

from . import db, socketio
from .printer import Printer, TestPrinter
from .models import Task, Print, User, db_lock
from .main import app, task_queue
from .websocket import send_print_state


app.app_context().push()
task_lock = Lock()


def finish_up_task(original_function):
    """
    Decorator function for setting complete = True in task table
    This function should be called in the worker code
    """

    global task_lock

    @wraps(original_function)
    def wrapper(*args, **kwargs):
        result = original_function(*args, **kwargs)

        job = get_current_job()
        with task_lock:
            if job:
                with db_lock:
                    task = Task.query.get(job.get_id())
                    if task:
                        task.complete = True
                        db.session.commit()
            return result

    return wrapper
        


@finish_up_task
def slice(user_id, data):
    try:
        # Validate data from the client
        original_filename = data['originalFileName']
        file_name = data['fileName']
        if data['quality'] == '1':
            quality = '0.15'
        elif data['quality'] == '2':
            quality = '0.2'
        elif data['quality'] == '3':
            quality = '0.3'
        else:
            app.logger.error(data['quality'])

        infill = data['infill'] 
        if int(infill) <= 0 and int(infill) >= 100:
            return 
        arg_quality = "layer_height=" 
        arg_infill = "infill_sparse_density=" 
        log_filename = file_name.split('.stl')[0] + '.log' 
        gcode_filename = file_name.replace('.stl', '.gcode') 

        # Launch CuraEngine from another process 
        code = app.config['CURA_ENGINE'] + " slice -v -j " + app.config['PRINTER_CONFIG_FILE'] \
            + " -s " +  arg_quality + quality + " -s " + arg_infill + infill + " -l " \
            + app.config['UPLOAD_FOLDER'] + file_name + " -o " + app.config['GCODE_FOLDER'] \
            + gcode_filename

        app.logger.debug(code)
        subp = subprocess.Popen(code.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, errors = subp.communicate()
        
        # Parsing the slicing info from the CuraEngine and write it to the gcode file for later printing
        header = errors.decode()
        regex = "Gcode header after slicing:\n(.*)\nEnd of gcode header\." 
        pattern = re.compile(regex, re.S) 
        target = pattern.search(header).group(1)
        with open(app.config['GCODE_FOLDER'] + gcode_filename, 'rt+') as f:
            f.write(target + '\n' + ';INFILL:{}\n;'.format(infill))
            f.seek(0)
            gcode = f.read()

            gcode = gcode.replace('M140 S0\n', '') # This two lines are for remove the unexpected
            gcode = gcode.replace('M104 S0\n', '') # command from the end of the gcode which might be 
                                                   # a bug from CuraEngine and it makes you to wait until
                                                   # printer temperature cooled down to 0 after printing
            f.seek(0)
            f.write(gcode)
        
        # Parsing information from CuraEngine and send it to client
        slice_info = {}
        for line in target.split('\n'): 
            if line.startswith(';'): 
                val = line.split(':') 
                slice_info[val[0][1:].strip()] = val[1].strip() 

        slice_info['fileName'] = original_filename 
        slice_info['state'] = 'success'
        # If client connection closed, a exception might be raised
    except timeouts.JobTimeoutException: 
        # On raspbery pi if server got slicing events in a row, server cpu temperature might be 
        # getting high which cause slicing time getting longer
        socketio.sleep(0)
        with db_lock:
            user = User.query.filter_by(id=user_id).first()
        socketio.emit(
                      'notify', 
                      'notice', 
                      'Server busy, Please try another time', 
                      '', 
                      'fas fa-exclamation-triangle', 
                      room=user.sid
        )
    finally: 
        socketio.sleep(0)
        with db_lock:
            user = User.query.filter_by(id=user_id).first()
        socketio.emit('slice', slice_info, room=user.sid)

        
@finish_up_task
def print(user_id, print_id, kwargs):
    try:
        printing_target = app.config['GCODE_FOLDER'] + kwargs['fileName'].replace('stl', 'gcode')

        with db_lock:
            # If the printing work was deleted by the user
            if not Print.query.filter_by(id=print_id).first():
                return 

        def get_current_print():
            with db_lock:
                return Print.query.filter_by(complete=False).order_by(Print.added_time.asc()).first()


        now_printing = get_current_print()
        with db_lock:
            now_printing.started_time_second = int(time.time())
            user = User.query.filter_by(id=user_id).first()
            user.on_print = True
            db.session.commit()

        # Uncomment the below line for actual printing
        # But it has several issue!
        # Because of the scheduling of operating system is not predictable 
        # If server gets a lots of load from client requests such as slicing event
        # Printing quality would be go down sometimes it'll stop printing
        # This seems like fundamental issue of setting printing process and web server process
        # On a same physical machine even after ajusting nice level and ionice level of the  
        # Processes didn't work
        # To handle this problem you need to seperate printing job from web server on a different
        # Physical machine

        if app.config['PRINT_MODE'] != 'demoprint':
            p = Printer() # For actual printing
        else:
            p = TestPrinter() # Fake printing for testing web interface

        job = get_current_job()

        # Printing job is working on the other thread
        t = threading.Thread(target=p.print_model, args=(printing_target,))
        t.start()

        # Checking status of current printing work in main thread
        prev_total_layer = 0
        prev_current_layer = 0
        while t.is_alive():
            if (p.total_layer != prev_total_layer) or (p.current_layer != prev_current_layer):
                prev_total_layer = p.total_layer
                prev_current_layer = p.current_layer
                now_printing = get_current_print()
                with db_lock:
                    now_printing.total_layer = p.total_layer
                    now_printing.current_layer = p.current_layer
                    db.session.commit() 
                send_print_state()
                
            time.sleep(1)
                
        # Take a snapshot of finished result
        url = app.config['SNAPSHOT_URI']
        path = app.config['PRINTED_MODEL_IMG_FOLDER']
        filename = now_printing.task_id + '.jpg'
        res = requests.get(url=url, stream=True)
        if res.status_code == 200:
            with open(path + filename, 'wb') as f:
                res.raw.decode_content = True
                shutil.copyfileobj(res.raw, f)

        now_printing = get_current_print()
        with db_lock:
            now_printing.complete = True
            now_printing.completed_time = str(datetime.utcnow())
            now_printing.infill_density = p.infill
            now_printing.filament_usage = p.filament_used
            now_printing.layer_height = p.layer_height
            user = User.query.filter_by(id=user_id).first()
            user.on_print = False
            db.session.commit()

        send_print_state()
        finish_unchecked = Print.query.filter_by(complete=True, user_checked=False, user_id=user_id).all()
        socketio.sleep(0)
        with db_lock:
            user = User.query.filter_by(id=user_id).first()
        socketio.emit('alarm', {'unchecked_count':len(finish_unchecked)}, room=user.sid)
    except Exception:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())

