import re
from flask import redirect, render_template, url_for, flash
from flask_login import login_required, logout_user, current_user

from . import auth, validate_password
from .forms import RegistrationForm, ResetPasswordRequestForm,\
                   ResetPasswordForm, DeleteUserForm, ChangePasswordForm
from .. import db, mail
from ..main import task_queue
from ..models import User, Task, Print, db_lock
from ..home.views import add_login_form
from ..home import get_alarm

  
@auth.route('/register', methods=['GET', 'POST'])
@add_login_form
def register(*args, **kwargs):
    from ..tasks import task_lock
    reg_form = RegistrationForm()
    if reg_form.validate_on_submit():
        # Register conditions, you should use email and user name that never used befor
        # and password must be contain at least 8 characters including a nuber and a letter
        # and you must checked agreement on terms
        with db_lock:
            if User.query.filter_by(email=reg_form.reg_email.data).first():
                flash({
                       'type':'notice',
                       'title':'Email already has been used',
                       'text':'Try use another email!',
                       'icon':'fas fa-at'
                }) 

            elif User.query.filter_by(username=reg_form.reg_username.data).first():
                flash({
                       'type':'notice',
                       'title':'Username already has been used',
                       'text':'Try use another username!',
                       'icon':'fas fa-user'
                }) 

                    
                
            elif not validate_password(reg_form.reg_password.data):
                flash({
                       'type':'notice',
                       'title':'Password must contain at least 8 characters including a number and a letter',
                       'text':'',
                       'icon':'fas fa-unlock-alt'
                }) 
            elif not reg_form.reg_agree_on_terms.data:
                flash({
                       'type':'notice',
                       'title':'You must agree on terms before register account',
                       'text':'',
                       'icon':'fas fa-file-alt'
                }) 
                
            else:
                # Putting a job in the work queue that sending a user verification email
                user = User(
                    email=reg_form.reg_email.data,
                    username=reg_form.reg_username.data,
                    user_id=reg_form.reg_email.data.split('@')[0],
                    password=reg_form.reg_password.data
                )
                db.session.add(user)
                db.session.commit()

                worker = 'src.email.send_email'
                key_string = 'verify_user'
                with task_lock:
                    job = task_queue.enqueue(worker,
                                             user, key_string,
                                             'Verify User Account',
                                             'email/verify_user.txt',
                                             'email/verify_user.html'
                    )
                    task = user.add_task(job.get_id(), worker, 'sending user verification mail')
                    db.session.add(task)
                    db.session.commit()

                flash({
                       'type':'info',
                       'title':'Email sent',
                       'text':'Please check your email',
                       'icon':'far fa-envelope'
                })
                
                return redirect(url_for('home.index'))
                


    login_form = kwargs['form'] if kwargs['form'] else None 
    return render_template('auth/register.html', reg_form=reg_form, login_form=login_form)



@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(
          {'type':'info',
           'title':'You have successfully been logged out.',
           'text':'See you next time!',
           'icon':'far fa-laugh-squint'
    })
    
    return redirect(url_for('home.index'))


@auth.route('/find_my_info', methods=['GET', 'POST'])
@add_login_form
def find_my_info(*args, **kwargs):
    from ..email import send_email
    from ..tasks import task_lock

    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    reset_request_form = ResetPasswordRequestForm()
    if reset_request_form.validate_on_submit():
        user = User.query.filter_by(email=reset_request_form.reset_request_email.data).first()
        if user:
            worker = 'src.email.send_email'
            key_string = 'reset_password'
            with task_lock:
                job = task_queue.enqueue(worker,
                                         user,
                                         key_string,
                                         'Reset Your Password',
                                         'email/reset_password.txt',
                                         'email/reset_password.html'
                )
                task = user.add_task(job.get_id(), worker, 'sending password reset info mail')
                with db_lock:
                    db.session.add(task)
                    db.session.commit()

        flash({
               'type':'info',
               'title':'Email sent',
               'text':'Please check your email',
               'icon':'far fa-envelope'
        })
        return redirect(url_for('home.index'))
    login_form = kwargs['form'] if kwargs['form'] else None
    return render_template('auth/find_my_info.html',
                           reset_request_form=reset_request_form,
                           login_form=login_form
    )


@auth.route('/delete_account', methods=['GET', 'POST'])
@add_login_form
def delete_account(*args, **kwargs):
    delete_user_form = DeleteUserForm()
    if current_user.is_authenticated:
        if delete_user_form.validate_on_submit():
            if current_user.verify_password(delete_user_form.delete_user_password.data):
                if current_user.on_print:
                    flash({
                           'type':'error',
                           'title':'Delete Account Failed',
                           'text':'You can\'t delete your account while printing',
                           'icon':'fas fa-exclamation-triangle'
                    })
                else:
                    with db_lock:
                        id = current_user.id
                        prints = Print.query.filter_by(user_id=id).all()
                        tasks = Task.query.filter_by(user_id=id).all()
                        user = User.query.filter_by(id=id).first()
                        for task in tasks:
                            db.session.delete(task)
                        for _print in prints:
                            db.session.delete(_print)
                        db.session.delete(user)
                        db.session.commit()
                    flash({
                           'type':'success',
                           'title':'Account deleted',
                           'text':'your accont has successfully deleted',
                           'icon':'fas fa-user-slash'
                    })
                return redirect(url_for('home.index'))
            else:
                flash({
                       'type':'error',
                       'title':'Password mismatched',
                       'text':'Please check your password',
                       'icon':'fas fa-key'
                })
    
     
    else:
        return redirect(url_for('home.index'))

    login_form = kwargs['form'] if kwargs['form'] else None
    return render_template('auth/delete_account.html',
                           alarm=get_alarm(),
                           delete_user_form=delete_user_form,
                           login_form=login_form
    )


@auth.route('/change_password', methods=['GET', 'POST'])
@add_login_form
def change_password(*args, **kwargs):
    change_password_form = ChangePasswordForm()
    if current_user.is_authenticated:
        if change_password_form.validate_on_submit():
            new_password = change_password_form.change_password.data
            if validate_password(new_password):
                current_user.password = new_password
                with db_lock:
                    db.session.commit()
                flash({
                       'type':'success',
                       'title':'Password changed',
                       'text':'Your password has been successfully changed',
                       'icon':'fas fa-key'
                })
                return redirect(url_for('home.index'))
            else:
                flash({
                       'type':'notice',
                       'title':'Password not allowed',
                       'text':'Password must contain at least 8 characters including a number and a letter',
                       'icon':'fas fa-unlock-alt'
                }) 
    else:
        return redirect(url_for('home.index'))
        
    login_form = kwargs['form'] if kwargs['form'] else None
    return render_template('auth/change_password.html', 
                           alarm=get_alarm(),
                           change_password_form=change_password_form,
                           login_form=login_form
    )


@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
@add_login_form
def reset_password(token, *args, **kwargs):
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    key_string = 'reset_password'
    user = User.verify_jwt_token(key_string, token)
    if not user:
        return redirect(url_for('home.index'))
    reset_form = ResetPasswordForm()
    if reset_form.validate_on_submit():
        new_password = reset_form.reset_password.data
        if validate_password(new_password):
            user.password = new_password
            with db_lock:
                db.session.commit()
            flash({
                   'type':'success',
                   'title':'Password changed',
                   'text':'Your password has been successfully changed',
                   'icon':'fas fa-key'
            })
            return redirect(url_for('home.index'))
        else:
            flash({
                   'type':'notice',
                   'title':'Password must contain at least 8 characters including a number and a letter',
                   'text':'',
                   'icon':'fas fa-unlock-alt'
            }) 
            
    login_form = kwargs['form'] if kwargs['form'] else None
    return render_template('auth/reset_password.html',
                           alarm=get_alarm(),
                           reset_form=reset_form,
                           login_form=login_form
    )


@auth.route('/verify_user/<token>', methods=['GET', 'POST'])
def verify_user(token, *args, **kwargs):
    if current_user.is_authenticated:
        return redirect(url_for('home.index'))
    key_string = 'verify_user'
    user = User.verify_jwt_token(key_string, token)
    if user:
        with db_lock:
            user.email_verified = True
            db.session.commit()
        flash({
               'type':'success',
               'title':'User account successfully verified!',
               'text':'You may now login.',
               'icon':'fas fa-user-plus'
        })
        return redirect(url_for('home.index'))

    return redirect(url_for('home.index'))



@auth.route('/user_info', methods=['GET', 'POST'])
@add_login_form
def user_info(*args, **kwargs):
    if current_user.is_authenticated:
        with db_lock:
            row = Print.query.filter_by(user_id=current_user.id, complete=True) \
                .order_by(Print.completed_time.desc()).first()

    login_form = kwargs['form'] if kwargs['form'] else None
    return render_template('auth/user_info.html',
                           user=current_user,
                           row=row,
                           alarm=get_alarm(),
                           login_form=login_form
    )

