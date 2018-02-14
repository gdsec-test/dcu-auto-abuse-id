import logging
from flask import request, current_app
from flask_restplus import Namespace, Resource, fields
from service.rest.custom_fields import Uri
from service.rest.helpers import validate_payload

_logger = logging.getLogger(__name__)

api = Namespace('classify',
                title='Automated Abuse Classifier API',
                description='Abuse classification operations',
                doc='/doc')

uri_input = api.model(
    'uri', {
        'uri': Uri(required=True, description='URI to classify')

    }
)

image_data_input = api.model(
    'image_data', {
        'image_id': fields.String(help='Image ID of existing DCU image', required=True),
        'target': fields.String(help='The brand being targeted if applicable'),
        'type': fields.String(help='Type of abuse associated with image', required=True, enum=['PHISHING', 'MALWARE', 'SPAM'])
    }
)

fields_to_return = api.model('response', {
    'target': fields.String(help='The Target of the abuse'),
    'uri': fields.String(help='The URI to classify'),
    'type': fields.String(help='The abuse type category'),
    'confidence': fields.String(help='A confidence score of 1 indicates an exact match, while 0 indicates no match'),
    'method': fields.String(help='The method used to obtain the confidence score.  Currently only: pHash'),
    'meta': fields.String(help='Additional metadata')
})


@api.route('/submit_uri', endpoint='classify')
class IntakeURI(Resource):

    @api.expect(uri_input)
    @api.marshal_with(fields_to_return, code=200)
    @api.response(200, 'Success', model=fields_to_return)
    @api.response(400, 'Validation Error')
    def post(self):
        """
        Submit URI for auto detection and classification
        Endpoint to handle intake of URIs reported as possibly containing abuse, which will then
        be parsed and evaluated to automatically determine how closely they match existing
        abuse fingerprints
        """
        payload = request.json
        validate_payload(payload, uri_input)
        classification_dict = current_app.config.get('phash').classify(payload.get('uri'))
        _logger.info('{}'.format(classification_dict))

        return classification_dict, 200


@api.route('/add_classification', endpoint='add')
class AddNewImage(Resource):

    @api.expect(image_data_input)
    @api.response(201, 'Success')
    @api.response(400, 'Validation Error')
    def put(self):
        payload = request.json
        phash = current_app.config.get('phash')
        success, reason = phash.add_classification(
            payload.get('image_id'),
            payload.get('type'),
            payload.get('target'))
        if success:
            return '', 201
        else:
            return reason, 500
