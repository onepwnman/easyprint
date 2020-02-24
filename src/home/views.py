from datetime import datetime
from flask import render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user
from werkzeug.urls import url_parse
from functools import wraps

from .forms import LoginForm
from ..models import User, Print, db_lock
from .. import db

from . import home, get_alarm


# 왼쪽 사이드바에 로그인 폼이 뜨는 페이지마다 아래의 데코레이터를 넣어준다. 
# blueprint route 함수마다 **kwargs로 인자를 준다.
def add_login_form(original_function):
    @wraps(original_function)
    def wrapper(*args, **kwargs):
        if current_user.is_anonymous:
            form = LoginForm()
            # TODO: autologin feature
            # TODO: 로그인 실패시 아이디는 form에 입력되어있어야함.
            if form.validate_on_submit():
                with db_lock:
                    user = User.query.filter_by(email=form.email.data).first()
                if user and user.verify_password(form.password.data):
                    if user.email_verified == True:
                        login_user(user, remember=form.auto_login.data)
                        next_page = request.args.get('next')
                        if not next_page or url_parse(next_page).netloc != '':
                            next_page = url_for('home.index')

                        with db_lock:
                            user.last_login = datetime.utcnow()
                            db.session.commit()
                        flash({
                               'type':'success',
                               'title':'Login Success',
                               'text':'Welcome! ' + str(user),
                               'icon':'far fa-check-circle'
                        })
                        return redirect(next_page)
                    else:
                        flash({
                               'type':'error',
                               'title':'Please check your email first',
                               'text':'Email verification is needed',
                               'icon':'far fa-envelope'
                        })
                        return redirect(url_for('home.index'))
                else:
                    flash({
                           'type':'error',
                           'title':'Invalid Email or Password',
                           'text':'Try it again!',
                           'icon':'fas fa-exclamation-triangle'
                    })
            kwargs['form'] = form

        elif current_user.is_authenticated:
            kwargs['form'] = None

        return original_function(*args, **kwargs)

    return wrapper 



@home.route('/', methods=['GET', 'POST'])
@home.route('/index', methods=['GET', 'POST'])
@add_login_form
def index(*args, **kwargs):
    login_form = kwargs['form'] if kwargs['form'] else None
    return render_template('home/index.html', login_form=login_form, alarm=get_alarm())



        
