import os
from urllib.parse import quote


class AppConfig(object):
    DBURL = 'localhost'
    DB = 'test'
    DB_PORT = 27017
    DB_USER = 'dbuser'
    DB_HOST = 'localhost'

    def __init__(self):
        self.CACHE_SERVICE = os.getenv('REDIS', 'localhost')


class ProductionAppConfig(AppConfig):
    DB = 'phishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_p_phishv2'
    TOKEN_AUTHORITY = 'sso.gdcorp.tools'
    DB_PASS = quote(os.getenv('DB_PASS', 'password'))
    DBURL = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}/?authSource={DB}'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'
    TOKEN_AUTHORITY = 'sso.ote-gdcorp.tools'
    DB_PASS = quote(os.getenv('DB_PASS', 'password'))
    DBURL = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}/?authSource={DB}'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_USER = 'devuser'
    TOKEN_AUTHORITY = 'sso.dev-gdcorp.tools'
    DB_PASS = quote(os.getenv('DB_PASS', 'password'))
    CLIENT_CERT = os.getenv("MONGO_CLIENT_CERT", '')
    DBURL = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}/?authSource={DB}&readPreference=primary&directConnection=true&tls=true&tlsCertificateKeyFile={CLIENT_CERT}'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class TestAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_USER = 'testuser'
    TOKEN_AUTHORITY = 'sso.dev-gdcorp.tools'
    DB_PASS = quote(os.getenv('DB_PASS', 'password'))
    CLIENT_CERT = quote(os.getenv("MONGO_CLIENT_CERT", ''))
    DBURL = f'mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}/?authSource={DB}&readPreference=primary&directConnection=true&tls=true&tlsCertificateKeyFile={CLIENT_CERT}'

    def __init__(self):
        super(TestAppConfig, self).__init__()


class TestingConfig(AppConfig):
    TOKEN_AUTHORITY = None
    CACHE_SERVICE = 'localhost'

    def __init__(self):
        self.DBURL = 'mongodb://localhost/devphishstory'
        self.DB_HOST = 'localhost'
        self.DB_PORT = 27017


config_by_name = {'dev': DevelopmentAppConfig,
                  'prod': ProductionAppConfig,
                  'ote': OTEAppConfig,
                  'test': TestingConfig}
