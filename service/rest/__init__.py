import os
from flask import Flask
from flask_restplus import Api, Resource, fields
from .api import api as ns1


def create_app(env):
    app = Flask(__name__)
    api = Api(
        app,
        version='1.0',
        title='DCU Classification API',
        description='Classifies URLs based on their detected abuse type',
        validate=True,
        doc='/doc',
    )
    api.add_namespace(ns1)
    return app
