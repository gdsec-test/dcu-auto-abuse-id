from flask import Flask
from flask_restplus import Api
from .api import api as ns1
from celery import Celery
from celeryconfig import CeleryConfig


def create_app(config):
    app = Flask(__name__)
    app.config.SWAGGER_UI_JSONEDITOR = True
    app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
    authorizations = {
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-KEY'
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
    api.add_namespace(ns1)
    return app
