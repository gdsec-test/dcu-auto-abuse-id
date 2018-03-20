import json
from flask import url_for
from mock import Mock
from flask_testing.utils import TestCase
import service.rest
from service.classifiers.phash import PHash


def resp(candidate, url=True):
    return dict(
        candidate=None,
        type='UNKNOWN',
        confidence=0.0,
        target=None,
        method='pHash',
        meta=dict())


class TestRest(TestCase):

    def create_app(self):
        return service.rest.create_app('test')

    def setUp(self):
        self.client = self.app.test_client()

    def test_classify_uri_success(self):
        self.client.application.config['phash'] = Mock(spec=PHash, classify=resp)
        data = dict(uri='https://localhost.com')
        response = self.client.post(
            url_for('classify_uri'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 200)

    def test_classify_bad_uri_request(self):
        data = dict()
        response = self.client.post(
            url_for('classify_uri'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    def test_classify_invalid_uri(self):
        data = dict(uri='http://localhost')
        response = self.client.post(
            url_for('classify_uri'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    def test_classify_image_success(self):
        self.client.application.config['phash'] = Mock(spec=PHash, classify=resp)
        data = dict(image_id='abc123')
        response = self.client.post(
            url_for('classify_image'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 200)

    def test_classify_bad_image_request(self):
        data = dict()
        response = self.client.post(
            url_for('classify_image'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    def test_classify_invalid_image_id(self):
        data = dict(image_id=12345)
        response = self.client.post(
            url_for('classify_image'),
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

    def test_missing_auth_key(self):
        self.client.application.config['phash'] = Mock(
            spec=PHash, add_classification=lambda x, y, z: (True, None))
        data = dict(image_id='someid', type='PHISHING', target='netflix')
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.put(
            url_for('add'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 401)

    def test_invalid_auth_key(self):
        self.client.application.config['phash'] = Mock(
            spec=PHash, add_classification=lambda x, y, z: (True, None))
        data = dict(image_id='someid', type='PHISHING', target='netflix')
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.put(
            url_for('add'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json',
                'X-API-KEY': 'blahblahblah'
            })
        self.assertEqual(response.status_code, 401)
