import os

from celery import Celery
from kombu import Exchange, Queue

from settings import AppConfig, config_by_name

config = config_by_name[os.getenv('sysenv', 'dev')]()


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

    def __init__(self, settings: AppConfig):
        self.broker_url = os.getenv('BROKER_URL')  # For local docker-compose testing
        if not self.broker_url:
            self.BROKER_PASS = settings.BROKER_PASS
            self.broker_url = settings.BROKER_URL

        self.result_backend = settings.DBURL
        self.mongodb_backend_settings = {
            'database': settings.DB,
            'taskmeta_collection': 'classifier-celery'
        }
        env = os.getenv('sysenv', 'dev')
        self.task_queues = CeleryConfig._getqueues(env)
        self.task_routes = CeleryConfig._getroutes(env)


def get_celery() -> Celery:
    capp = Celery()
    capp.config_from_object(CeleryConfig(config))
    return capp
