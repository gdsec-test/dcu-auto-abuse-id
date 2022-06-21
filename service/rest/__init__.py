import os

from csetutils.flask import instrument
from flask import Flask

from service.cache.redis_cache import RedisCache

from .api import api as ns1


def create_app(config):
    app = Flask(__name__)
    app.config.SWAGGER_UI_JSONEDITOR = True
    app.config.SWAGGER_UI_DOC_EXPANSION = 'list'
    app.config['token_authority'] = config.TOKEN_AUTHORITY
    app.config['cache'] = RedisCache(config.CACHE_SERVICE)
    app.register_blueprint(ns1)
    instrument(app, 'auto-abuse-id', env=os.getenv('sysenv', 'dev'), sso=config.TOKEN_AUTHORITY, excluded_paths=[
        '/doc/',
        '/classify/health'
    ], min_status_code=300)

    return app
