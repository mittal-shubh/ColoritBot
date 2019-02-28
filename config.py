import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'WHATisthis123'
    SQLALCHEMY_DATABASE_URI = 'postgres://ghlbmbaqnmrgbj:6496a6e9d0a1d61b043ee38846f3ccd067e6dd8c8e2468081dc0a123461c6003@ec2-54-204-2-25.compute-1.amazonaws.com:5432/d89st8fqh2n622'

class ProductionConfig(Config):
    DEBUG = False

class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True

class TestingConfig(Config):
    TESTING = True