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
    BUCKET_WEIGHTS = [1, 2, 3, 4, 5] # how to weigh each bucket
    # the number of buckets is derived from the number of weights
    # the spacing between each bucket is determined by the minimum confidence requested

    def __init__(self):
        self.DB_PASS = urllib.quote(PasswordDecrypter.decrypt(os.getenv('DB_PASS'))) if os.getenv('DB_PASS') \
            else 'password'
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB)


class ProductionAppConfig(AppConfig):
    DB = 'phishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_p_phish'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = '10.22.188.208'
    DB_USER = 'devuser'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class TestingConfig(AppConfig):
    DBURL = 'mongodb://localhost/devphishstory'
    COLLECTION = 'test'
    DB_HOST = 'localhost'
    DB_PORT = 27017
    # Setting this again here as tests are dependent on these exact values
    BUCKET_WEIGHTS = [1, 2, 3, 4, 5]


config_by_name = {'dev': DevelopmentAppConfig,
                  'prod': ProductionAppConfig,
                  'ote': OTEAppConfig,
                  'test': TestingConfig}
