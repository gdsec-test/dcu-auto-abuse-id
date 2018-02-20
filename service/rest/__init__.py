from flask import Flask
from flask_restplus import Api
from .api import api as ns1
from service.classifiers.phash import PHash
from settings import config_by_name


def create_app(env):
    app = Flask(__name__)
    app.config.SWAGGER_UI_JSONEDITOR = True
    app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
    api = Api(
        app,
        version='1.0',
        title='DCU Classification API',
        description='Classifies URLs/Images based on their detected abuse type',
        validate=True,
        doc='/doc',
    )
    config = config_by_name[env]()
    phash = PHash(config)
    app.config['phash'] = phash
    api.add_namespace(ns1)
    return app
