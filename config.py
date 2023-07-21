# config.py

class Config(object):
    """
    Cấu hình chung
    """
    # Đưa các config env vào đây
    SECRET_KEY = 'hung doan'

    MYSQL_DATABASE_HOST = 'localhost'
    MYSQL_DATABASE_DB = 'blogs'
    MYSQL_DATABASE_USER = 'root'
    MYSQL_DATABASE_PASSWORD = 'Anhhung040100'



class DevelopmentConfig(Config):
    """
    Cấu hình môi trường development
    """

    DEBUG = True
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    """
    Cấu hình môi trường production
    """

    DEBUG = False

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}