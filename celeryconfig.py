import os
import urllib

from kombu import Exchange, Queue

from encryption_helper import PasswordDecrypter


class CeleryConfig:
    BROKER_TRANSPORT = 'pyamqp'
    BROKER_USE_SSL = True
    CELERYD_CONCURRENCY = 1
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json', 'pickle']
    CELERY_IMPORTS = 'run'
    CELERYD_HIJACK_ROOT_LOGGER = False
    CELERY_SEND_EVENTS = False

    def __init__(self, settings):
        self.BROKER_PASS = os.getenv('BROKER_PASS', 'password')
        self.BROKER_PASS = urllib.quote(PasswordDecrypter.decrypt(self.BROKER_PASS))
        self.BROKER_URL = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@rmq-dcu.int.godaddy.com:5672/grandma'
        # Messages sent to dcu-classifier
        self.CELERY_ROUTES = {
            'run.classify': {'queue': settings.PHASHQUEUE, 'routing_key': settings.PHASHQUEUE},
            'run.add_classification': {'queue': settings.PHASHQUEUE, 'routing_key': settings.PHASHQUEUE}
        }
