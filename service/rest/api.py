import json
import logging
from functools import wraps

from flask import current_app, request
from flask_restplus import Namespace, Resource, fields
from gd_auth.token import AuthToken

from service.rest.custom_fields import Uri
from service.rest.helpers import validate_payload

_logger = logging.getLogger(__name__)

FULL_DAY = 86400
HALF_HOUR = 1800

# Phash celery endpoints
CLASSIFY_ROUTE = 'classify.request'
SCAN_ROUTE = 'scan.request'


api = Namespace('classify',
                title='Automated Abuse Classifier API',
                description='Abuse classification operations',
                )

scan_input = api.model(
    'scan_input', {
        'uri': Uri(required=True, description='URI to scan'),
        'sitemap': fields.Boolean(help='True if the URI represents a sitemap', required=False, default=False)
    }
)

classify_input = api.model(
    'input', {
        'uri': Uri(required=False, description='URI to classify')
    }
)

classification_resource = api.model(
    'classification_response', {
        'id':
            fields.String(
                help='A unique ID for the task',
                example='1234',
                required=True
            ),
        'status':
            fields.String(
                help='The current status of the task',
                enum=['PENDING', 'STARTED', 'COMPLETE'],
                required=True
            ),
        'confidence':
            fields.Float(
                help='level of confidence in the classification',
                example=0.0,
                required=True,
                default=0.0
            ),
        'candidate':
            fields.String(
                help='The candidate being scanned',
                example='http://example.com',
                required=True
            )
    }
)

scan_resource = api.model(
    'scan_response', {
        'id':
            fields.String(
                help='A unique ID for the task',
                example='1234',
                required=True
            ),
        'status':
            fields.String(
                help='The current status of the task',
                enum=['PENDING', 'STARTED', 'COMPLETE'],
                required=True
            ),
        'uri':
            Uri(
                description='URL scanned',
                required=True
            ),
        'sitemap':
            fields.Boolean(
                help='True if the URI represents the location of a sitemap',
                required=True
            )
    }
)


def token_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth_groups = current_app.config.get('auth_groups')
        token_authority = current_app.config.get('token_authority')
        endpoint = args[0].endpoint

        if not token_authority:  # bypass if no token authority is set
            return f(*args, **kwargs)

        token = request.headers.get('Authorization', '').strip()
        if not token:
            return {'message': 'Authorization header not provided'}, 401

        if token.startswith('sso-jwt'):
            token = token[8:].strip()

        try:
            auth_token = AuthToken.parse(token, token_authority, 'auto-abuse-id', 'jomax')
            if auth_groups[endpoint]:
                if not set(auth_token.payload.get('groups')) & set(auth_groups[endpoint]):
                    return {'message': 'Authenticated user is not allowed access'}, 403
            _logger.debug('{}: authenticated'.format(auth_token.payload.get('accountName')))
        except Exception:
            return {'message': 'Error in authorization'}, 401
        return f(*args, **kwargs)
    return wrapped


@api.route('/health', endpoint='health')
class Health(Resource):

    @api.response(200, 'OK')
    def get(self):
        """
        Health check endpoint
        """
        return 'OK', 200


@api.route('/scan', endpoint='scan')
class IntakeScan(Resource):

    @api.expect(scan_input)
    @api.marshal_with(scan_resource, code=201)
    @api.response(201, 'Success', model=scan_resource)
    @api.response(400, 'Validation Error')
    @api.response(401, 'Unauthorized')
    @api.doc(security='apikey')
    @token_required
    def post(self):
        """
        Submit URI for scanning and potential Abuse API ticket creation.
        Writes entry to REDIS using URI as key, which lasts 30 minutes. If another request for
        the same URI is received within 30 minutes, the REDIS record is returned.
        """
        payload = request.json
        _logger.info('Provided Payload for scan: {}'.format(payload))
        validate_payload(payload, scan_input)
        uri = payload.get('uri')

        cache = current_app.config.get('cache')
        cached_val = cache.get(uri)
        if cached_val:
            return json.loads(cached_val), 201

        result = current_app.config.get('celery').send_task(SCAN_ROUTE, args=(payload,))
        scan_resp = dict(id=result.id, status='PENDING', uri=uri, sitemap=payload.get('sitemap'))
        cache.add(uri, json.dumps(scan_resp), ttl=FULL_DAY)
        _logger.info('{}'.format(scan_resp))

        return scan_resp, 201


@api.route('/scan/<string:jid>', endpoint='scanresult')
class ScanResult(Resource):

    @api.marshal_with(scan_resource, code=200)
    @api.response(200, 'Success', model=scan_resource)
    @api.response(401, 'Unauthorized')
    @api.response(404, 'Invalid scan ID')
    @api.doc(security='apikey')
    @token_required
    def get(self, jid):
        """
        Obtain the results or status of a previously submitted scan request.
        Writes entry to REDIS using JID as key, which lasts for 24 hours. Any requests received
        for the same JID within that 24 hour window will receive the record data from REDIS.
        """
        cache = current_app.config.get('cache')
        cached_val = cache.get(jid)
        if cached_val:
            return json.loads(cached_val), 200

        asyn_res = current_app.config.get('celery').AsyncResult(jid)
        status = asyn_res.state
        if asyn_res.ready():
            res = asyn_res.get()
            res['status'] = status
            cache.add(jid, json.dumps(res), ttl=FULL_DAY)
            return res

        return dict(id=jid, status=status)


@api.route('/classification', endpoint='classification')
class IntakeResource(Resource):

    @api.expect(classify_input)
    @api.marshal_with(classification_resource, code=201)
    @api.response(201, 'Success', model=classification_resource)
    @api.response(401, 'Unauthorized')
    @api.response(400, 'Validation Error')
    @api.doc(security='apikey')
    @token_required
    def post(self):
        """
        Submit URI for auto detection and classification.
        Endpoint to handle intake of URIs reported as possibly containing abuse.
        Writes entry to REDIS using URI as key, which lasts 30 minutes. If another request for
        the same URI is received within 30 minutes, the REDIS record is returned.
        """
        payload = request.json
        _logger.info('Provided Payload for classification: {}'.format(payload))
        validate_payload(payload, classify_input)
        uri = payload.get('uri')

        cache = current_app.config.get('cache')
        cached_val = cache.get(uri)
        if cached_val:
            return json.loads(cached_val), 201

        result = current_app.config.get('celery').send_task(CLASSIFY_ROUTE, args=(payload,))
        classification_resp = dict(id=result.id, status='PENDING', candidate=uri)
        cache.add(uri, json.dumps(classification_resp), ttl=HALF_HOUR)
        _logger.info('{}'.format(classification_resp))

        return classification_resp, 201


@api.route('/classification/<string:jid>', endpoint='classificationresult')
class ClassificationResult(Resource):

    @api.marshal_with(classification_resource, code=200)
    @api.response(200, 'Success', model=classification_resource)
    @api.response(401, 'Unauthorized')
    @api.response(404, 'Invalid classification ID')
    @api.doc(security='apikey')
    @token_required
    def get(self, jid):
        """
        Obtain the results or status of a previously submitted classification request.
        Writes entry to REDIS using JID as key, which lasts for 24 hours. Any requests received
        for the same JID within that 24 hour window will receive the record data from REDIS.
        """
        cache = current_app.config.get('cache')
        cached_val = cache.get(jid)
        if cached_val:
            return json.loads(cached_val), 200

        asyn_res = current_app.config.get('celery').AsyncResult(jid)
        status = asyn_res.state
        if asyn_res.ready():
            res = asyn_res.get()
            res['status'] = status
            cache.add(jid, json.dumps(res), ttl=FULL_DAY)
            return res

        return dict(id=jid, status=status)
