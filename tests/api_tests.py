import json
from collections import namedtuple

from celery import Celery
from flask import url_for
from flask_testing.utils import TestCase
from mock import patch, MagicMock

import service.rest
from mock_redis import MockRedis
from settings import config_by_name


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
        app = service.rest.create_app(config_by_name['test']())
        app.config.get('cache')._redis = MockRedis()
        return app

    def setUp(self):
        self.client = self.app.test_client()

    @patch.object(Celery, "send_task")
    def test_classify_uri_success(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('abc123')
        data = dict(uri='https://localhost.com')
        response = self.client.post(
            url_for('classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 201)

    def test_classify_invalid_request(self):
        data = dict(uri='http://localhost', image_id='blah')
        response = self.client.post(
            url_for('classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    def test_classify_invalid_uri(self):
        data = dict(uri='http://localhost')
        response = self.client.post(
            url_for('classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    @patch.object(Celery, "send_task")
    def test_classify_image_success(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('some_jid')
        data = dict(image_id='abc1234')
        response = self.client.post(
            url_for('classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 201)

    @patch.object(Celery, "send_task")
    def test_classify_image_success_cache(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('some_id')
        data = dict(image_id='abc123')
        response = self.client.post(
            url_for('classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 201)
        send_task_method.return_value = namedtuple('Resp', 'id')('some_other_id')
        data = dict(image_id='abc123')
        response = self.client.post(
            url_for('classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        resp_data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(resp_data.get('id'), 'some_id')

    @patch.object(Celery, 'AsyncResult')
    def test_get_classify_pending(self, mock_result):
        mock_result.return_value = MagicMock(state='PENDING', ready=lambda: False)
        response = self.client.get(
            url_for('classification') + '/some_id')
        resp_data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)

    @patch.object(Celery, 'AsyncResult')
    def test_get_classify_complete_cached(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='some_id', status='SUCCESS'))
        response = self.client.get(
            url_for('classification') + '/some_id')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            url_for('classification') + '/some_id')
        resp_data = json.loads(response.data)
        self.assertEqual(resp_data.get('status'), 'SUCCESS')

    @patch.object(Celery, "send_task")
    def test_add_classification_success(self, send_task_method):
        send_task_method.return_value = True
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
