import logging
from flask import request, current_app
from flask_restplus import Namespace, Resource, fields, abort
from service.rest.custom_fields import Uri
from service.rest.helpers import validate_payload
from functools import wraps
from auth.AuthToken import AuthToken

_logger = logging.getLogger(__name__)

# Phash celery endpoints
CLASSIFY_ROUTE = 'classify.request'
SCAN_ROUTE = 'scan.request'
FINGERPRINT_ROUTE = 'fingerprint.request'


api = Namespace('classify',
                title='Automated Abuse Classifier API',
                description='Abuse classification operations',
                )

scan_input = api.model(
    'scan_input', {
        'uri': Uri(required=True, description='URI to scan'),
        'sitemap': fields.Boolean(help='True if the URI represents a sitemap', required=False)
    }
)

classify_input = api.model(
    'input', {
        'uri': Uri(required=False, description='URI to classify'),
        'image_id': fields.String(help='Image ID of existing DCU image', required=False, example='abc123')
    }
)

image_data_input = api.model(
    'image_data', {
        'image_id': fields.String(help='Image ID of existing DCU image', required=True, example='abc123'),
        'target': fields.String(help='The brand being targeted if applicable', example='Netflix'),
        'type': fields.String(help='Type of abuse associated with image', required=True, enum=['PHISHING',
                                                                                               'MALWARE',
                                                                                               'SPAM'])
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
        'target':
            fields.String(
                help='Brand being targeted',
                example='NETFLIX'
            ),
        'candidate':
            fields.String(
                help='The candidate being scanned',
                example='http://example.com',
                required=True
            ),
        'meta':
            fields.String(
                help='Additional metadata'
            ),
        'type':
            fields.String(
                help='The type of abuse that was detected',
                required=True,
                enum=['PHISHING', 'MALWARE', 'SPAM', 'UNKNOWN']
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

        if not token_authority:  # bypass if no token authority is set
            return f(*args, **kwargs)

        token = request.headers.get('X-API-KEY')
        if not token:
            return {'message': 'API token is missing'}, 401

        try:
            auth_token = AuthToken.parse(token, token_authority, 'jomax')
            if not set(auth_token.payload.get('groups')) & set(auth_groups):
                return {'message': 'Unauthorized'}, 401
            _logger.info('{}: authenticated'.format(auth_token.payload.get('accountName')))
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
        return '', 200


@api.route('/scan', endpoint='scan')
class IntakeScan(Resource):

    @api.expect(scan_input)
    @api.marshal_with(scan_resource, code=201)
    @api.response(201, 'Success', model=scan_resource)
    @api.response(400, 'Validation Error')
    def post(self):
        """
        Submit URI for scanning and potential Abuse API ticket creation
        """
        payload = request.json
        validate_payload(payload, scan_input)

        result = current_app.config.get('celery').send_task(SCAN_ROUTE, args=(payload,))
        scan_resp = dict(id=result.id, status='PENDING')
        _logger.info('{}'.format(scan_resp))

        return scan_resp, 201


@api.route('/scan/<string:id>', endpoint='scanresult')
class ScanResult(Resource):

    @api.marshal_with(scan_resource, code=200)
    @api.response(200, 'Success', model=scan_resource)
    @api.response(404, 'Invalid scan ID')
    def get(self, id):
        """
        Obtain the results or status of a previously submitted scan request
        """
        asyn_res = current_app.config.get('celery').AsyncResult(id)
        status = asyn_res.state
        if asyn_res.ready():
            res = asyn_res.get()
            res['status'] = status
            return res

        return dict(id=id, status=status)


@api.route('/classification', endpoint='classification')
class IntakeResource(Resource):

    @api.expect(classify_input)
    @api.marshal_with(classification_resource, code=201)
    @api.response(201, 'Success', model=classification_resource)
    @api.response(400, 'Validation Error')
    def post(self):
        """
        Submit URI for auto detection and classification
        Endpoint to handle intake of URIs reported as possibly containing abuse, which will then
        be parsed and evaluated to automatically determine how closely they match existing
        abuse fingerprints
        """
        payload = request.json
        validate_payload(payload, classify_input)
        uri = payload.get('uri')
        image = payload.get('image_id')
        if uri and image:
            abort(400, 'uri and image are mutually exclusive')
        else:
            candidate = uri or image
            result = current_app.config.get('celery').send_task(CLASSIFY_ROUTE, args=(payload,))
            classification_resp = dict(id=result.id, status='PENDING', candidate=candidate)
            _logger.info('{}'.format(classification_resp))
            return classification_resp, 201


@api.route('/classification/<string:id>', endpoint='classificationresult')
class ClassificationResult(Resource):

    @api.marshal_with(classification_resource, code=200)
    @api.response(200, 'Success', model=classification_resource)
    @api.response(404, 'Invalid classification ID')
    def get(self, id):
        """
        Obtain the results or status of a previously submitted classification request
        """
        asyn_res = current_app.config.get('celery').AsyncResult(id)
        status = asyn_res.state
        if asyn_res.ready():
            res = asyn_res.get()
            res['status'] = status
            return res

        return dict(id=id, status=status)


@api.route('/fingerprint', endpoint='add')
class AddNewImage(Resource):

    @api.expect(image_data_input)
    @api.response(201, 'Success')
    @api.response(400, 'Validation Error')
    @api.doc(security='apikey')
    @token_required
    def put(self):
        """
        Add a classification for an existing DCU image
        Hashes an existing DCU image for use in future classification requests
        """
        payload = request.json
        result = current_app.config.get('celery').send_task(FINGERPRINT_ROUTE, args=(payload,))
        return None, 201
