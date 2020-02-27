import os 

class Config(object):
    """
    Common configurations
    """
    DEBUG = True
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'u can never guess this looooooooooooong flag'
    RECAPTCHA_USE_SSL = True
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024
    ALLOWED_FILE_NAME_LENGTH = 64
    SQLALCHEMY_DATABASE_URI = 'mysql://root@localhost/easyprint'
    SERVER_ADDRESS = '0.0.0.0'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = [os.environ.get('ADMINS')]
    PRINT_MODE = os.environ.get('PRINT_MODE') or 'demoprint'

    SERVER = 'http://localhost'
    MJPG_PORT = 5001
    MJPG_SERVER = SERVER + ':' + str(MJPG_PORT)
    SNAPSHOT_URI = MJPG_SERVER + '/?action=snapshot'
    WEBCAM_URI = MJPG_SERVER + '/?action=stream'


    
    SOURCE_DIR = os.environ.get('SOURCE_DIR') or 'src'
    BASEDIR = os.environ.get('BASEDIR')
    IMG_FOLDER = BASEDIR + '/src/static/img/'
    UPLOAD_FOLDER = BASEDIR + '/src/static/modeling/'
    GCODE_FOLDER = BASEDIR + '/src/static/gcode/'
    PRINTED_MODEL_IMG_FOLDER = IMG_FOLDER + '/model_img/'

    folder_list = [UPLOAD_FOLDER, GCODE_FOLDER, PRINTED_MODEL_IMG_FOLDER]
    for folder in folder_list:
        if not os.path.exists(folder):
            os.mkdir(folder)

    CURA_ENGINE = BASEDIR + '/util/CuraEngine/build/CuraEngine'
    PRINTER_CONFIG_FILE = BASEDIR + '/settings/printer/anet_a8.def.json'
    TEMPDIR = BASEDIR + '/tmp/'

class DevelopmentConfig(Config):
    """
    Development configurations
    """

    SERVER = 'http://localhost'
    SERVER_PORT = 12000


class ProductionConfig(Config):
    """
    Production configurations
    """

    DEBUG = False
    SERVER_PORT = 4000
    SERVER = 'https://easyprint.hopto.org/'


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root@localhost/easyprint_test'


app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

