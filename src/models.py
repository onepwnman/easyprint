import os
import json
import time
import jwt

from datetime import datetime
from hashlib import md5
from multiprocessing import Lock
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.declarative import DeclarativeMeta

from src import db, login

db_lock = Lock()


class AlchemyUserEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            blacklist = [
                'complete',
                'filament_usage',
                'user_id',
                'query_class',
                'completed_time',
                'hashed_filename',
                'user_checked',
                'infill_density',
                'query',
                'id',
            ]
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    if field in blacklist:
                        continue

                    if field == 'started_time_second':
                        data = int(time.time()) - data    

                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    if isinstance(data, datetime):
                        fields[field] = str(data)
                    else:
                        fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), index=True, unique=True)
    user_id = db.Column(db.String(64), index=True, unique=True)
    username = db.Column(db.String(64), index=True)
    password_hash = db.Column(db.String(128))
    sid = db.Column(db.String(64), index=True)
    is_admin = db.Column(db.Boolean, default=False)
    on_print = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    tasks = db.relationship('Task', backref='user', lazy='dynamic')
    print = db.relationship('Print', backref='user', lazy='dynamic')


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute.')


    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)


    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


    def __repr__(self):
        return '{}'.format(self.username)

    
    def add_task(self, task_id, worker, description):
        task = Task(id=task_id, name=worker, description=description, user=self)
        return task


    def get_task_in_progress(self, worker):
        global db_lock

        with db_lock:
            return Task.query.filter_by(name=worker, user=self, complete=False).first() 


    def get_jwt_token(self, key_str, expires_in=600):
        from src.main import app
        return jwt.encode(
            {key_str:self.id, 'exp':time.time() + expires_in},
             app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)


    @staticmethod
    def verify_jwt_token(key_str, token):
        from src.main import app
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])[key_str]
        except Exception:
            return 
        return User.query.get(id)


class Task(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(128), index=True)
    description = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    complete = db.Column(db.Boolean, default=False)
    added_time = db.Column(db.DateTime, default=datetime.utcnow)

    
class Print(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(64), index=True)
    hashed_filename = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    username = db.Column(db.String(64), index=True)
    user_checked = db.Column(db.Boolean, default=False)
    complete = db.Column(db.Boolean, default=False)
    added_time = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_time_second = db.Column(db.Integer)
    started_time_second = db.Column(db.Integer)
    total_layer = db.Column(db.Integer, default=0)
    current_layer = db.Column(db.Integer, default=0)
    completed_time = db.Column(db.DateTime, index=True)
    filament_usage = db.Column(db.String(16))
    layer_height = db.Column(db.String(8))
    infill_density = db.Column(db.String(8))
    task_id = db.Column(db.String(36)) 
        

@login.user_loader
def load_user(user_id):
    global db_lock

    with db_lock:
        return User.query.get(int(user_id))

