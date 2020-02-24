import json 
import sys

from flask_socketio import emit
from flask_login import current_user
from flask import request

from . import socketio, db
from .main import app, task_queue, conn
from .models import Task, Print, User, AlchemyUserEncoder, db_lock


def send_print_state():
    with db_lock:
        rows = Print.query.filter_by(complete=False).order_by(Print.added_time.asc()).all()
    if rows:
        socketio.sleep(0)
        socketio.emit('print', json.dumps(rows, cls=AlchemyUserEncoder), broadcast=True)
    else:
        socketio.sleep(0)
        socketio.emit('print', {}, broadcast=True)
        

def send_print_state_client(sid):
    with db_lock:
        rows = Print.query.filter_by(complete=False).order_by(Print.added_time.asc()).all()
    if rows:
        socketio.sleep(0)
        emit('print', json.dumps(rows, cls=AlchemyUserEncoder), room=sid)
    else:
        socketio.sleep(0)
        socketio.emit('print', {}, room=sid)
    

@socketio.on('connect')
def connect_handler():
    try:
        id = current_user.id
        with db_lock:
            user = User.query.filter_by(id=id).first()
            user.sid = request.sid
            db.session.commit()
    except AttributeError:
        #  Anonymous user
        app.logger.debug('hello UnKnown!')
    send_print_state_client(request.sid)


@socketio.on('delete')
def delete_handler(json_data):
    try:
        if json_data['user'] == current_user.username:
            with db_lock:
                now_printing = Print.query.filter_by(complete=False) \
                    .order_by(Print.added_time.asc()).first()
                if json_data['added_time'] == now_printing.added_time:
                    app.logger.error('You can\'t stop current running printing')
                    raise 

                _print = Print.query.filter_by(username=json_data['user'],
                                               added_time=json_data['added_time']
                ).first()
                _task = Task.query.filter_by(id=_print.task_id).first()
                db.session.delete(_task)
                db.session.delete(_print)
                db.session.commit() 

    except Exception:
        # Anonymouse user 
        app.logger.error('execption', exc_info=sys.exc_info())
    finally:
        send_print_state()


@socketio.on('slice')
def slice_handler(data):   # data is Dict
    from .tasks import task_lock

    worker = 'src.tasks.slice'
    if current_user.get_task_in_progress(worker):
        socketio.sleep(0)
        with db_lock:
            room = User.query.filter_by(id=current_user.id).first().sid
        emit('slice', {
                       'state':'fail',
                       'type':'notice',
                       'title':'Slicing is already in progress!',
                       'text':'Please wait for the previous task',
                       'icon':'fas fa-spinner fa-pulse'
                      },
                      room=room
        )
    else:
        with task_lock:
            job = task_queue.enqueue(worker, current_user.id, data)
            task = current_user.add_task(job.get_id(), worker, 'turning stl file to gcode file')
            with db_lock:
                db.session.add(task)
                db.session.commit()
    

@socketio.on('print')
def print_handler(data):   # data is Dict
    from .tasks import task_lock

    worker = 'src.tasks.print'

    with db_lock:
        task_in_progress = Task.query.filter_by(name=worker, complete=False) \
            .order_by(Task.added_time.desc()).first()

    print_job = Print(filename=data['originalFileName'],
                      hashed_filename=data['fileName'].strip('.stl'),
                      user_id=current_user.id, username=current_user.username,
                      estimated_time_second=data['estimatedTime']
    )
    with db_lock:
        db.session.add(print_job)
        db.session.commit()

    with task_lock:
        try:
            if task_in_progress:
                job = task_queue.enqueue(worker,
                                         current_user.id,
                                         print_job.id,
                                         data,
                                         job_timeout=-1,
                                         depends_on=task_in_progress.id
                )
            else:
                job = task_queue.enqueue(worker,
                                         current_user.id,
                                         print_job.id,
                                         data,
                                         job_timeout=-1
                )
            task = current_user.add_task(job.get_id(), worker, 'printing object from gcode file')
        except NoSuchJobError:
            app.logger.debug('Job successfully delete')

        with db_lock:
            print_job.task_id = job.get_id()
            db.session.add(task)
            db.session.commit()

    send_print_state()
    socketio.sleep(0)
    with db_lock:
        room = User.query.filter_by(id=current_user.id).first().sid
    emit('notify', {
                    'type':'info',
                    'title':'Your job is successfully added to the printing list!',
                    'text':'',
                    'icon':'fas fa-check-circle'
                    }, room=room
    )
    emit('camera', {'button':'on'}, room=room)

