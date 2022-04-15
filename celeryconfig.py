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
    WORKER_ENABLE_REMOTE_CONTROL = False

    @staticmethod
    # TODO CMAPT-5032: remove queue_type argument
    def _getqueues(env, queue_type):
        queue_modifier = ''
        exchange = 'classifier'
        if env != 'prod':
            queue_modifier = env
            exchange = env + exchange
        return (
            Queue(queue_modifier + 'classify_tasks', exchange=Exchange(exchange, type='topic'),
                  routing_key='classify.request', queue_arguments={'x-queue-type': queue_type}),
            Queue(queue_modifier + 'scan_tasks', exchange=Exchange(exchange, type='topic'),
                  routing_key='scan.request', queue_arguments={'x-queue-type': queue_type})
        )

    @staticmethod
    # TODO CMAPT-5032: remove queue_type argument
    def _getroutes(env, queue_type):
        queue_modifier = ''
        if env != 'prod':
            queue_modifier = env
        return {
            'classify.request':
                {'queue': Queue(queue_modifier + 'classify_tasks', Exchange(queue_modifier + 'classify_tasks'),
                                routing_key='classify.request', queue_arguments={'x-queue-type': queue_type})},
            'scan.request':
                {'queue': Queue(queue_modifier + 'scan_tasks', Exchange(queue_modifier + 'scan_tasks'),
                                routing_key='scan.request', queue_arguments={'x-queue-type': queue_type})}
        }

    def __init__(self, settings: AppConfig):
        # TODO CMAPT-5032: remove QUEUE TYPE and just set broker url to multiple brokers
        queue_type = os.getenv('QUEUE_TYPE')
        self.broker_url = os.getenv('MULTIPLE_BROKERS') if queue_type == 'quorum' else os.getenv('SINGLE_BROKER')

        self.result_backend = settings.DBURL
        self.mongodb_backend_settings = {
            'database': settings.DB,
            'taskmeta_collection': 'classifier-celery'
        }
        env = os.getenv('sysenv', 'dev')
        # TODO CMAPT-5032: remove queue_type argument
        self.task_queues = CeleryConfig._getqueues(env, queue_type)
        self.task_routes = CeleryConfig._getroutes(env, queue_type)


def get_celery() -> Celery:
    global __celery
    if not __celery:
        __celery = Celery()
        __celery.config_from_object(CeleryConfig(config))
    return __celery
