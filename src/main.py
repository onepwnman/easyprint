#!/usr/bin/env  python3
import eventlet
eventlet.monkey_patch()
import os 

from redis import Redis
from rq import Queue, Worker, Connection, exceptions
from multiprocessing import Process


REDIS_URI = os.environ.get('REDIS_URI') or 'redis://localhost:6379'
conn = Redis.from_url(REDIS_URI)
task_queue = Queue('easyprint_tasks', connection=conn)

from . import create_app

app_config = os.getenv('FLASK_ENV')
if app_config != 'development':
    app_config = 'production'

app = create_app(app_config)

def run_server():
    from . import tasks, websocket

    global app
    global app_config

    def worker(connection):
        global task_queue

        with Connection(connection):
            worker = Worker([task_queue])
            worker.work()
      
    mq = Process(target=worker, args=(conn,))
    mq.start()
    
    if app_config == 'development':
        from . import socketio
        socketio.run(app, host=app.config['SERVER_ADDRESS'],
                     port=app.config['SERVER_PORT'], debug=True)
    elif app_config == 'production':
        eventlet.wsgi.server(eventlet.listen(('', app.config['SERVER_PORT'])), app)


