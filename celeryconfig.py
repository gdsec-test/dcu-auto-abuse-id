import os

from celery import Celery
from kombu import Exchange, Queue

from settings import AppConfig, config_by_name

config = config_by_name[os.getenv('sysenv', 'dev')]()
__celery = None


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = not os.getenv('DISABLESSL', False)  # True unless local docker-compose testing
    worker_concurrency = 1
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json', 'pickle']
    imports = 'run'
    worker_hijack_root_logger = False
    worker_send_task_events = False
    task_track_started = True
    WORKER_ENABLE_REMOTE_CONTROL = True

    @staticmethod
    def _getqueues(env, queue_args):
        queue_modifier = ''
        exchange = 'classifier'
        if env != 'prod':
            queue_modifier = env
            exchange = env + exchange
        return (
            Queue(queue_modifier + 'classify_tasks', exchange=Exchange(exchange, type='topic'),
                  routing_key='classify.request', queue_arguments=queue_args),
            Queue(queue_modifier + 'scan_tasks', exchange=Exchange(exchange, type='topic'),
                  routing_key='scan.request', queue_arguments=queue_args)
        )

    @staticmethod
    def _getroutes(env, queue_args):
        queue_modifier = ''
        if env != 'prod':
            queue_modifier = env
        return {
            'classify.request':
                {'queue': Queue(queue_modifier + 'classify_tasks', Exchange(queue_modifier + 'classify_tasks'),
                                routing_key='classify.request', queue_arguments=queue_args)},
            'scan.request':
                {'queue': Queue(queue_modifier + 'scan_tasks', Exchange(queue_modifier + 'scan_tasks'),
                                routing_key='scan.request', queue_arguments=queue_args)}
        }

    def __init__(self, settings: AppConfig):
        self.broker_url = os.getenv('MULTIPLE_BROKERS')

        self.result_backend = settings.DBURL
        self.mongodb_backend_settings = {
            'database': settings.DB,
            'taskmeta_collection': 'classifier-celery'
        }
        env = os.getenv('sysenv', 'dev')

        queue_args = {'x-queue-type': 'quorum'}
        self.task_queues = CeleryConfig._getqueues(env, queue_args)
        self.task_routes = CeleryConfig._getroutes(env, queue_args)


def get_celery() -> Celery:
    global __celery
    if not __celery:
        __celery = Celery()
        __celery.config_from_object(CeleryConfig(config))
    return __celery
