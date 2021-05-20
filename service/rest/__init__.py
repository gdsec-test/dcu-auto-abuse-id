from celery import Celery
from dcustructuredloggingflask.flasklogger import add_request_logging
from flask import Flask
from flask_restplus import Api

from celeryconfig import CeleryConfig
from service.cache.redis_cache import RedisCache

from .api import api as ns1


def create_app(config):
    app = Flask(__name__)
    app.config.SWAGGER_UI_JSONEDITOR = True
    app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
    authorizations = {
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization'
        }
    }
    api = Api(
        app,
        version='1.0',
        title='DCU Classification API',
        description='Classifies URLs/Images based on their detected abuse type',
        validate=True,
        doc='/doc',
        authorizations=authorizations
    )
    app.config['token_authority'] = config.TOKEN_AUTHORITY
    app.config['auth_groups'] = config.AUTH_GROUPS
    celery = Celery()
    celery.config_from_object(CeleryConfig(config))
    app.config['celery'] = celery
    app.config['cache'] = RedisCache(config.CACHE_SERVICE)
    api.add_namespace(ns1)

    add_request_logging(app, 'auto-abuse-api', sso=config.TOKEN_AUTHORITY, excluded_paths=[
        '/doc/',
        '/classify/health'
    ], min_status_code=300)

    return app
