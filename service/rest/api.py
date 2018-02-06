import os
import logging

from flask import request
from settings import config_by_name
from flask_restplus import Namespace, Resource
from service.classifiers.phash import PHash


api = Namespace('validator', description='Validator operations')
env = os.getenv('sysenv', 'dev')
config = config_by_name[env]()
phash = PHash(config)
master_db = {}


@api.route('/submit_uri')
class IntakeURI(Resource):
    """
    Class to handle intake of URIs reported as possibly containing abuse, which will then
     be parsed and evaluated to automatically determine how closely they match existing
     abuse fingerprints
    """
    _logger = logging.getLogger(__name__)

    def get(self):
        """
        Displays all URIs submitted along with the number of times submitted
        :return:
        """
        return {'Submitted URIs': master_db}

    def put(self):
        """
        Adds URIs submitted to the _archive dict, keeping count of number of times submitted
        :return:
        """
        uri = request.form['uri']

        classification_dict = phash.classify(uri)
        self._logger.info('{}'.format(classification_dict))

        target = request.form.get('verified', False)
        if target and not classification_dict.get('target', False):
            classification_dict['target'] = 'reported:{}'.format(target)

        master_db[uri] = (master_db[uri] + 1) if master_db.get(uri, None) else 1

        return classification_dict


@api.route('/status_uri')
class StatusURI(Resource):
    """
    Class to provide status on a specific URI which has already been submitted to the API
    """

    def put(self):
        """
        Displays the status of the URI, if previously submitted
        :return:
        """
        uri = request.form['uri']
        message = '{} has not been submitted'.format(uri)
        if master_db.get(uri, False):
            message = '{} has already been classified'.format(uri)
        return {'status': message}
