from re import match, search
from flask import Blueprint

auth = Blueprint('auth', __name__)

# Password must contain at least 8 characters including a number and a letter
def validate_password(password):
    flag = True
    password_pattern = r'[A-Za-z0-9@#$%^&+=]{8,}'

    if not match(password_pattern, password):
        flag = False
    elif not search("[A-Za-z]", password):
        flag = False
    elif not search("[0-9]", password):
        flag = False

    return flag


from . import views
