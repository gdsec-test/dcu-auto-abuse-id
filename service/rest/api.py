import os
import logging

from settings import config_by_name
from flask_restplus import Namespace, Resource, fields, inputs, reqparse
from service.classifiers.phash import PHash

_logger = logging.getLogger(__name__)
api = Namespace('classify',
                title='Automated Abuse Classifier API',
                description='Abuse classification operations',
                validate=True,
                doc='/doc')

env = os.getenv('sysenv', 'dev')
config = config_by_name[env]()
phash = PHash(config)

parser = reqparse.RequestParser(bundle_errors=True)
parser.add_argument('uri',
                    required=True,
                    type=inputs.url,
                    help='{error_msg}',
                    location='json')

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

    @api.doc('classify_uri', parser=parser)
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
        args = parser.parse_args()
        uri = args.get('uri', False)

        classification_dict = phash.classify(uri)
        _logger.info('{}'.format(classification_dict))

        return classification_dict, 201
