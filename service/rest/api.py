import json
import logging
from functools import wraps

from flask import Blueprint, current_app, request
from gd_auth.token import AuthToken, TokenBusinessLevel
from marshmallow import Schema, ValidationError, fields, validates_schema

from celeryconfig import get_celery

_logger = logging.getLogger(__name__)

FULL_DAY = 86400
HALF_HOUR = 1800
KEY_CACHE = 'cache'
KEY_CELERY = 'celery'
KEY_STATUS = 'status'
KEY_URI = 'uri'
PENDING = 'PENDING'

# Phash celery endpoints
CLASSIFY_ROUTE = 'classify.request'
SCAN_ROUTE = 'scan.request'

CLASSIFY_REDIS_PREFIX = 'clas'
SCAN_REDIS_PREFIX = 'scan'
api = Blueprint('classify', __name__, url_prefix='/classify')


class MetadataSchema(Schema):
    customerId = fields.String()
    orionGuid = fields.String()
    entitlementId = fields.String()
    product = fields.String()

    @validates_schema
    def orion_or_entitlement_validation(self, data, **kwargs):
        if 'orionGuid' not in data and data.get('orionGuid', '') == '' and 'entitlementId' not in data and data.get('entitlementId', '') == '':
            raise ValidationError('one of orionGuid or entitlementId is required')


class ScanInput(Schema):
    uri = fields.URL()
    sitemap = fields.Bool()
    metadata = fields.Nested(MetadataSchema)


class ClassifyInput(Schema):
    uri = fields.URL()


def token_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        token_authority = current_app.config.get('token_authority')

        if not token_authority:  # bypass if no token authority is set
            return f(*args, **kwargs)

        token = request.headers.get('Authorization', '').strip()
        if not token:
            return {'message': 'Authorization header not provided'}, 401

        if token.startswith('sso-jwt'):
            token = token[8:].strip()

        try:
            auth_token = AuthToken.parse(token, token_authority, 'auto-abuse-id', 'jomax')

            # Throws on failure.
            auth_token.is_expired(TokenBusinessLevel.LOW)
            _logger.debug('{}: authenticated'.format(auth_token.payload.get('accountName')))
        except Exception as e:
            _logger.exception(e)
            return {'message': 'Error in authorization'}, 401
        return f(*args, **kwargs)
    return wrapped


@api.route('/health', methods=['GET'], endpoint='health')
def healthcheck():
    """
    Health check endpoint
    """
    return 'OK', 200


@api.route('/scan', methods=['POST'], endpoint='scan')
@token_required
def create_scan_job():
    """
    Submit URI for scanning and potential Abuse API ticket creation.
    Writes entry to REDIS using URI as key, which lasts 30 minutes. If another request for
    the same URI is received within 30 minutes, the REDIS record is returned.
    """
    payload = request.json
    _logger.info(f'Provided Payload for scan: {payload}')
    try:
        schema = ScanInput()
        schema.load(payload)
        uri = payload.get(KEY_URI)
        _unique_redis_key = f'{SCAN_REDIS_PREFIX}:{uri}'

        cache = current_app.config.get(KEY_CACHE)
        cached_val = cache.get(_unique_redis_key)
        if cached_val:
            return json.loads(cached_val), 201

        result = get_celery().send_task(SCAN_ROUTE, args=(payload,))
        scan_resp = dict(id=result.id, status=PENDING, uri=uri, sitemap=payload.get('sitemap'))
        cache.add(_unique_redis_key, json.dumps(scan_resp), ttl=FULL_DAY)
        _logger.info(f'{scan_resp}')
        return scan_resp, 201
    except Exception as e:
        return {'message': str(e)}, 400


@api.route('/scan/<jid>', methods=['GET'], endpoint='scanresult')
@token_required
def get_scan_job(jid):
    """
    Obtain the results or status of a previously submitted scan request.
    Writes entry to REDIS using JID as key, which lasts for 24 hours. Any requests received
    for the same JID within that 24 hour window will receive the record data from REDIS.
    """
    _unique_redis_key = f'{SCAN_REDIS_PREFIX}:{jid}'
    cache = current_app.config.get(KEY_CACHE)
    cached_val = cache.get(_unique_redis_key)
    if cached_val:
        return json.loads(cached_val), 200

    asyn_res = get_celery().AsyncResult(jid)
    status = asyn_res.state
    if asyn_res.ready():
        res = asyn_res.get()
        res[KEY_STATUS] = status
        cache.add(_unique_redis_key, json.dumps(res), ttl=FULL_DAY)
        return res, 200

    return dict(id=jid, status=status), 200


@api.route('/classification', methods=['POST'], endpoint='classification')
@token_required
def create_classify_job():
    """
    Submit URI for auto detection and classification.
    Endpoint to handle intake of URIs reported as possibly containing abuse.
    Writes entry to REDIS using URI as key, which lasts 30 minutes. If another request for
    the same URI is received within 30 minutes, the REDIS record is returned.
    """
    payload = request.json
    try:
        schema = ClassifyInput()
        _logger.info(f'Provided Payload for classification: {payload}')
        schema.load(payload)
        uri = payload.get(KEY_URI)
        _unique_redis_key = f'{CLASSIFY_REDIS_PREFIX}:{uri}'

        cache = current_app.config.get(KEY_CACHE)
        cached_val = cache.get(_unique_redis_key)
        if cached_val:
            return json.loads(cached_val), 201

        result = get_celery().send_task(CLASSIFY_ROUTE, args=(payload,))
        classification_resp = dict(id=result.id, status=PENDING, candidate=uri)
        cache.add(_unique_redis_key, json.dumps(classification_resp), ttl=HALF_HOUR)
        _logger.info(f'{classification_resp}')

        return classification_resp, 201
    except Exception as e:
        return {'message': str(e)}, 400


@api.route('/classification/<jid>', methods=['GET'], endpoint='classificationresult')
@token_required
def get_classification_result(jid):
    """
    Obtain the results or status of a previously submitted classification request.
    Writes entry to REDIS using JID as key, which lasts for 24 hours. Any requests received
    for the same JID within that 24 hour window will receive the record data from REDIS.
    """
    _unique_redis_key = f'{CLASSIFY_REDIS_PREFIX}:{jid}'
    cache = current_app.config.get(KEY_CACHE)
    cached_val = cache.get(_unique_redis_key)
    if cached_val:
        return json.loads(cached_val), 200

    asyn_res = get_celery().AsyncResult(jid)
    status = asyn_res.state
    if asyn_res.ready():
        res = asyn_res.get()
        res[KEY_STATUS] = status
        cache.add(_unique_redis_key, json.dumps(res), ttl=FULL_DAY)
        return res, 200
    return dict(id=jid, status=status), 200
