import os

from flask import Flask, request
from flask_restplus import Api, Resource


env = os.getenv('sysenv', 'dev')
debug = False if env == 'prod' else True

app = Flask(__name__)
api = Api(app)


@api.route('/submit_uri')
class ParseURI(Resource):
    '''
    Class to handle intake of URIs reported as possibly containing abuse, which will then
     be parsed and evaluated to automatically determine how closely they match existing
     abuse fingerprints
    '''
    _archive = {}

    def get(self):
        '''
        Displays all URIs submitted along with the number of times submitted
        :return:
        '''
        return {'Submitted URIs': self._archive}

    def put(self):
        '''
        Adds URIs submitted to the _archive dict, keeping count of number of times submitted
        :return:
        '''
        uri = request.form['uri']
        self._archive[uri] = (self._archive[uri] + 1) if self._archive.get(uri, None) else 1
        return {'submit_uri': 'URI queued for parsing: {}'.format(uri)}


if __name__ == '__main__':
    app.run(debug=debug)
