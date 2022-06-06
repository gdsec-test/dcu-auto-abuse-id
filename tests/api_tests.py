import json
from collections import namedtuple

from celery import Celery
from flask import url_for
from flask_testing.utils import TestCase
from mock import MagicMock, patch

import service.rest
from settings import config_by_name
from tests.mock_redis import MockRedis


class TestRest(TestCase):

    def create_app(self):
        app = service.rest.create_app(config_by_name['test']())
        app.config.get('cache')._redis = MockRedis()
        return app

    def setUp(self):
        self.client = self.app.test_client()

    ''' Scan Tests '''

    def test_scan_invalid_uri(self):
        data = dict(uri='http://localhost')
        response = self.client.post(
            url_for('classify.scan'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    @patch.object(Celery, 'send_task')
    def test_scan_uri_success_cache(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('some_id')
        data = dict(uri='https://1localhost.com')
        response = self.client.post(
            url_for('classify.scan'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 201)
        send_task_method.return_value = namedtuple('Resp', 'id')('some_other_id')
        data = dict(uri='https://1localhost.com')
        response = self.client.post(
            url_for('classify.scan'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        resp_data = json.loads(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(resp_data.get('id'), 'some_id')

    @patch.object(Celery, 'AsyncResult')
    def test_get_scan_pending(self, mock_result):
        mock_result.return_value = MagicMock(state='PENDING', ready=lambda: False)
        response = self.client.get(url_for('classify.scan') + '/123')
        self.assertEqual(response.status_code, 200)

    @patch.object(Celery, 'AsyncResult')
    def test_get_scan_complete_cached(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='123', status='SUCCESS'))
        response = self.client.get(url_for('classify.scan') + '/123')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url_for('classify.scan') + '/123')
        resp_data = json.loads(response.data)
        self.assertEqual(resp_data.get('status'), 'SUCCESS')

    @patch.object(Celery, 'AsyncResult')
    def test_get_scan_complete_cached_missing_auth_key(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='123', status='SUCCESS'))
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.get(
            url_for('classify.scan') + '/123',
            headers={
                'Content-Type': 'application/json'
            }
        )
        self.assertEqual(response.status_code, 401)

    @patch.object(Celery, 'AsyncResult')
    def test_get_scan_complete_cached_invalid_auth_key(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='123', status='SUCCESS'))
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.get(
            url_for('classify.scan') + '/123',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'blahblahblah'
            }
        )
        self.assertEqual(response.status_code, 401)

    ''' Classify Tests '''

    @patch.object(Celery, 'send_task')
    def test_classify_uri_success(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('abc123')
        data = dict(uri='https://localhost.com')
        response = self.client.post(
            url_for('classify.classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 201)

    def test_classify_invalid_uri(self):
        data = dict(uri='http://localhost')
        response = self.client.post(
            url_for('classify.classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 400)

    @patch.object(Celery, 'AsyncResult')
    def test_get_classify_pending(self, mock_result):
        mock_result.return_value = MagicMock(state='PENDING', ready=lambda: False)
        response = self.client.get(
            url_for('classify.classification') + '/some_id')
        self.assertEqual(response.status_code, 200)

    @patch.object(Celery, 'AsyncResult')
    def test_get_classify_complete_cached(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='some_id', status='SUCCESS'))
        response = self.client.get(
            url_for('classify.classification') + '/some_id')
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            url_for('classify.classification') + '/some_id')
        resp_data = json.loads(response.data)
        self.assertEqual(resp_data.get('status'), 'SUCCESS')

    @patch.object(Celery, 'send_task')
    def test_classify_uri_invalid_auth_key(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('abc123')
        data = dict(uri='https://localhost.com')
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.post(
            url_for('classify.classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'blahblahblah'
            })
        self.assertEqual(response.status_code, 401)

    @patch.object(Celery, 'send_task')
    def test_classify_uri_missing_auth_key(self, send_task_method):
        send_task_method.return_value = namedtuple('Resp', 'id')('abc123')
        data = dict(uri='https://localhost.com')
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.post(
            url_for('classify.classification'),
            data=json.dumps(data),
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 401)

    @patch.object(Celery, 'AsyncResult')
    def test_get_classify_complete_cached_invalid_auth_key(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='some_id', status='SUCCESS'))
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.get(
            url_for('classify.classification') + '/some_id',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'blahblahblah'
            })
        self.assertEqual(response.status_code, 401)

    @patch.object(Celery, 'AsyncResult')
    def test_get_classify_complete_cached_missing_auth_key(self, mock_result):
        mock_result.return_value = MagicMock(
            state='SUCCESS',
            ready=lambda: True,
            get=lambda: dict(id='some_id', status='SUCCESS'))
        self.client.application.config['token_authority'] = 'sso.dev-godaddy.com'
        response = self.client.get(
            url_for('classify.classification') + '/some_id',
            headers={
                'Content-Type': 'application/json'
            })
        self.assertEqual(response.status_code, 401)
