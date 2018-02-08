import os
import logging
from settings import config_by_name
from flask import request
from flask_restplus import Namespace, Resource, fields, inputs, reqparse
from custom_fields import Uri
from service.classifiers.phash import PHash
from helpers import validate_payload

_logger = logging.getLogger(__name__)
api = Namespace('classify',
                title='Automated Abuse Classifier API',
                description='Abuse classification operations',
                doc='/doc')

env = os.getenv('sysenv', 'dev')
config = config_by_name[env]()
phash = PHash(config)

uri_input = api.model(
    'uri', {
        'uri': Uri(required=True, description='URI to classify')

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


@api.route('/submit_uri')
class IntakeURI(Resource):

    @api.expect(uri_input)
    @api.marshal_with(fields_to_return, code=201)
    @api.response(201, 'Success', model=fields_to_return)
    @api.response(400, 'Validation Error')
    def put(self):
        """
        Submit URI for auto detection and classification
        Endpoint to handle intake of URIs reported as possibly containing abuse, which will then
        be parsed and evaluated to automatically determine how closely they match existing
        abuse fingerprints
        """
        payload = request.json
        validate_payload(payload, uri_input)
        classification_dict = phash.classify(payload.get('uri'))
        _logger.info('{}'.format(classification_dict))

        return classification_dict, 201
