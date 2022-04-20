import os
from collections import defaultdict
from urllib.parse import quote


class AppConfig(object):
    DBURL = 'localhost'
    DB = 'test'
    DB_PORT = 27017
    DB_USER = 'dbuser'
    DB_HOST = 'localhost'
    AUTH_GROUPS = defaultdict(list)

    def __init__(self):
        self.DB_PASS = quote(os.getenv('DB_PASS', 'password'))
        self.DBURL = 'mongodb://{}:{}@{}/?authSource={}'.format(self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB)
        self.AUTH_GROUPS['add'] = ['DCU-Phishstory']
        self.CACHE_SERVICE = os.getenv('REDIS', 'localhost')


class ProductionAppConfig(AppConfig):
    DB = 'phishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_p_phishv2'
    TOKEN_AUTHORITY = 'sso.godaddy.com'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'
    TOKEN_AUTHORITY = 'sso.ote-godaddy.com'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = '10.36.156.188'
    DB_USER = 'devuser'
    TOKEN_AUTHORITY = 'sso.dev-godaddy.com'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class TestAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = '10.36.156.188'
    DB_USER = 'testuser'
    TOKEN_AUTHORITY = 'sso.dev-godaddy.com'

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
