import json
from flask import url_for
from mock import Mock
from flask_testing.utils import TestCase
import service.rest
from service.classifiers.phash import PHash


class TestRest(TestCase):

    def create_app(self):
        return service.rest.create_app('test')

    def setUp(self):
        self.client = self.app.test_client()

    def test_classify_success(self):
        self.client.application.config['phash'] = Mock()
        data = dict(uri='https://localhost.com')
        response = self.client.post(
            url_for('classify'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 200)

    def test_classify_bad_request(self):
        data = dict()
        response = self.client.post(
            url_for('classify'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    def test_classify_bad_uri(self):
        data = dict(uri='http://localhost')
        response = self.client.post(
            url_for('classify'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    def test_add_classification_success(self):
        self.client.application.config['phash'] = Mock(spec=PHash, add_classification=lambda x, y, z: (True, None))
        data = dict(image_id='someid', type='PHISHING', target='netflix')
        response = self.client.put(
            url_for('add'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 201)

    def test_add_classification_bad_request(self):
        data = dict(image_id='someid')
        response = self.client.put(
            url_for('add'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)
