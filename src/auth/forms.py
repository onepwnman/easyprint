from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, ValidationError, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo

from ..models import User, db_lock

class RegistrationForm(FlaskForm):
    reg_email = StringField('Email', validators=[DataRequired(), Email()])
    reg_username = StringField('Username', validators=[DataRequired()])
    reg_password = PasswordField('Password', validators=[ DataRequired(),
                                  EqualTo('reg_confirm_password', message='Passwords must match') ])
    reg_confirm_password = PasswordField('Confirm Password')
    reg_agree_on_terms = BooleanField('회원약관에 동의합니다.(필수)')
    reg_submit = SubmitField('Register')

    def validate_email(self, field):
        with db_lock:
            if User.query.filter_by(email=field.data).first():
                raise ValidationError('Email is already is use.')

    def validate_username(self, field):
        with db_lock:
            if User.query.filter_by(username=field.data).first():
                raise ValidationError('Username is already in use.')


class ResetPasswordRequestForm(FlaskForm):
    reset_request_email = StringField('Email', validators=[DataRequired(), Email()])
    reset_request_submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    reset_password = PasswordField('Password', validators=[DataRequired()])
    reset_password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('reset_password')])
    reset_submit = SubmitField('Request Password Reset') 


class DeleteUserForm(FlaskForm):
    delete_user_password = PasswordField('Password', validators=[DataRequired()])
    delete_user_submit = SubmitField('Delete User Account')


class ChangePasswordForm(FlaskForm):
    change_password = PasswordField('Password', validators=[DataRequired()])
    change_password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('change_password')])
    change_password_submit = SubmitField('Change Password') 
  

