import os
import urllib

from kombu import Exchange, Queue


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
    CELERY_TRACK_STARTED = True

    @staticmethod
    def _getqueues(env):
        queue_modifier = ''
        exchange = 'classifier'
        if env != 'prod':
            queue_modifier = env
            exchange = env + exchange
        return (
            Queue(queue_modifier + 'classify_tasks', exchange=Exchange(exchange, type='topic'),
                  routing_key='classify.request'),
            Queue(queue_modifier + 'scan_tasks', exchange=Exchange(exchange, type='topic'),
                  routing_key='scan.request')
        )

    @staticmethod
    def _getroutes(env):
        queue_modifier = ''
        if env != 'prod':
            queue_modifier = env
        return {
            'classify.request': {'queue': queue_modifier + 'classify_tasks', 'routing_key': 'classify.request'},
            'scan.request': {'queue': queue_modifier + 'scan_tasks', 'routing_key': 'scan.request'}
        }

    def __init__(self, settings):
        self.BROKER_PASS = urllib.quote(os.getenv('BROKER_PASS', 'password'))
        self.BROKER_URL = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@rmq-dcu.int.godaddy.com:5672/grandma'

        self.CELERY_RESULT_BACKEND = settings.DBURL
        self.CELERY_MONGODB_BACKEND_SETTINGS = {
            'database': settings.DB,
            'taskmeta_collection': 'classifier-celery'
        }
        env = os.getenv('sysenv', 'test')
        self.CELERY_QUEUES = CeleryConfig._getqueues(env)
        self.CELERY_ROUTES = CeleryConfig._getroutes(env)
