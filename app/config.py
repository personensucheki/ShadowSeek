import os


class BaseConfig:
    # SECRET_KEY muss zwingend als Umgebungsvariable gesetzt werden!
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///shadowseek.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True  # Nur über HTTPS in Produktion
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 Stunde
    WTF_CSRF_ENABLED = True

class DevConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False

class ProdConfig(BaseConfig):
    DEBUG = False
