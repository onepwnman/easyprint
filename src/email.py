from flask import render_template
from flask_mail import Message
from src import mail
from src.tasks import finish_up_task


def _send_email(subject, sender, recipients, text_body, html_body, attachments=None):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    if attachments:
        for attachment in attachments:
            msg.attach(*attachment)
    mail.send(msg)
    

@finish_up_task
def send_email(user, key_str, title, text_body, html_body):
    from .main import app
    # test_request_context is needed for mail server to find easyprint server
    with app.app_context(), app.test_request_context(base_url=app.config['SERVER']):
        token = user.get_jwt_token(key_str)
        _send_email('[Easyprint] ' + title,
                    sender=app.config['ADMINS'][0],
                    recipients=[user.email],
                    text_body=render_template(text_body, user=user, token=token),
                    html_body=render_template(html_body, user=user, token=token))



      

