import os
import urllib

from encryption_helper import PasswordDecrypter


class AppConfig(object):
    DBURL = 'localhost'
    DB = 'test'
    DB_PORT = 27017
    DB_USER = 'dbuser'
    DB_HOST = 'localhost'
    COLLECTION = 'fingerprints'
    LOGGING_COLLECTION = 'logs'
    TOKEN_AUTHORITY = 'sso.dev-godaddy.com'
    AUTH_GROUPS = ['DCU-Phishstory']

    def __init__(self):
        self.DB_PASS = urllib.quote(PasswordDecrypter.decrypt(os.getenv('DB_PASS'))) if os.getenv('DB_PASS') \
            else 'password'
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB)


class ProductionAppConfig(AppConfig):
    DB = 'phishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_p_phish'
    TOKEN_AUTHORITY = 'sso.godaddy.com'
    PHASHQUEUE = 'phash_classify'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'
    TOKEN_AUTHORITY = 'sso.ote-godaddy.com'
    PHASHQUEUE = 'otephash_classify'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = '10.22.188.208'
    DB_USER = 'devuser'
    PHASHQUEUE = 'devphash_classify'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class TestingConfig(AppConfig):
    DBURL = 'mongodb://localhost/devphishstory'
    COLLECTION = 'test'
    DB_HOST = 'localhost'
    DB_PORT = 27017
    TOKEN_AUTHORITY = 'placeholder'  # bypass
    PHASHQUEUE = 'placeholder'


config_by_name = {'dev': DevelopmentAppConfig,
                  'prod': ProductionAppConfig,
                  'ote': OTEAppConfig,
                  'test': TestingConfig}
