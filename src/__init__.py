from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_assets import Environment, Bundle
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

db = SQLAlchemy()
login = LoginManager()
migrate = Migrate()
bootstrap = Bootstrap()
socketio = SocketIO()
mail = Mail()


from .config import app_config

def create_app(config_name):
    global db
    global login
    global migrate
    global bootstrap
    global socketio
    global mail

    from .main import REDIS_URI

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])

    db.init_app(app)
    bootstrap.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    socketio = SocketIO(app, message_queue=REDIS_URI)
    login.init_app(app)
    login.login_view = "home.index"
    login.login_message = {
                           'type':'notice',
                           'title':'Login required',
                           'text':'You must be logged in to access this page.',
                           'icon':'fas fa-sign-in-alt'
    }

    assets = Environment(app)
    assets.url = app.static_url_path
    assets.debug = True

    scss = Bundle('scss/selectable.scss', filters='pyscss', output='css/selectable.css')
    assets.register('scss_all', scss)


    from src import models

    from .home import home as home_blueprint
    app.register_blueprint(home_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    from .printer import printer as printer_blueprint 
    app.register_blueprint(printer_blueprint)


    from .home.views import add_login_form 

    @app.errorhandler(403)
    @add_login_form
    def page_not_found(*args, **kwargs):
        login_form = kwargs['form'] if kwargs['form'] else None
        return render_template('errors/403.html', login_form=login_form), 403

    @app.errorhandler(404)
    @add_login_form
    def page_not_found(*args, **kwargs):
        login_form = kwargs['form'] if kwargs['form'] else None
        return render_template('errors/404.html', login_form=login_form), 404

    @app.errorhandler(500)
    @add_login_form
    def page_not_found(*args, **kwargs):
        login_form = kwargs['form'] if kwargs['form'] else None
        return render_template('errors/500.html', login_form=login_form), 500



    return app
