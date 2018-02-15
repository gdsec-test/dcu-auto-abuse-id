import requests
from mock import patch
from collections import namedtuple
from nose.tools import assert_true, assert_false
from service.utils.urihelper import URIHelper


class TestURIHelper:

    @classmethod
    def setup(cls):
        cls._urihelper = URIHelper()
        cls.test_url = 'http://someurlthatscool.com'

    @patch.object(requests.Session, 'request')
    def test_resolves_403(self, mocked_method):
        status = dict(status_code=403, status_message='FORBIDDEN')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        assert_true(self._urihelper.resolves(self.test_url))

    @patch.object(requests.Session, 'request')
    def test_resolves_406(self, mocked_method):
        status = dict(status_code=406, status_message='UNACCEPTABLE')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        assert_true(self._urihelper.resolves(self.test_url))

    @patch.object(requests.Session, 'request')
    def test_resolves_200(self, mocked_method):
        status = dict(status_code=200, status_message='SUCCESS')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        assert_true(self._urihelper.resolves(self.test_url))

    @patch.object(requests.Session, 'request')
    def test_resolves_301(self, mocked_method):
        status = dict(status_code=301, status_message='MOVED')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        assert_true(self._urihelper.resolves(self.test_url))

    @patch.object(requests.Session, 'request')
    def test_resolves_100(self, mocked_method):
        status = dict(status_code=100, status_message='CONTINUE')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        assert_true(self._urihelper.resolves(self.test_url))

    @patch.object(requests.Session, 'request')
    def test_resolves_500(self, mocked_method):
        status = dict(status_code=500, status_message='FAIL')
        mocked_method.return_value = namedtuple('struct', status.keys())(**status)
        assert_false(self._urihelper.resolves(self.test_url))
