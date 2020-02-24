from flask import Blueprint
from flask_login import current_user
from ..models import db_lock, Print
from ..models import Print

home = Blueprint('home', __name__)

def get_alarm():
    try:
        with db_lock:
            unchecked = Print.query.filter_by(user_id=current_user.id, 
                                              complete=True,
                                              user_checked=False).all()
        alarm = len(unchecked) 
    except AttributeError:
        alarm = 0
    return alarm
    


from . import views
