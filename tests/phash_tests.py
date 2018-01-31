import mongomock
from nose.tools import assert_true, assert_false
from service.classifiers.phash import PHash
from settings import TestingConfig
from mock import patch, Mock


def return_bytes(file_name):
    with open(file_name, mode='rb') as f:
        return (True, f.read())


class TestPhash:

    @classmethod
    def setup_class(cls):
        config = TestingConfig()
        cls._phash = PHash(config)
        # Mock db
        cls._phash._collection = mongomock.MongoClient().db.collection
        cls._phash._collection.insert_many([{
            "target": "amazon",
            "chunk3": "62e2",
            "chunk2": "b023",
            "chunk1": "bf37",
            "type": "PHISHING",
            "chunk4": "62e2",
        }, {
            "target": "netflix",
            "chunk3": "2f0e",
            "chunk2": "0585",
            "chunk1": "afbf",
            "type": "PHISHING",
            "chunk4": "8585",
        }, {
            "target": "amazon",
            "chunk3": "6ec4",
            "chunk2": "913b",
            "chunk1": "ae7b",
            "type": "PHISHING",
            "chunk4": "e0c0",
        }])

    def test_phash_match(self):
        self._phash._validate = Mock(return_value=return_bytes('tests/images/phash_match.png'))
        data = self._phash.classify('some url')
        assert_true(data.get('type') == 'PHISHING')
        assert_true(data.get('confidence') == 1.0)
        assert_true(data.get('target') == 'amazon')

    def test_phash_miss(self):
        self._phash._validate = Mock(return_value=return_bytes('tests/images/maaaaybe.jpg'))
        data = self._phash.classify('some url')
        assert_true(data.get('type') == 'UNKNOWN')
        assert_true(data.get('confidence') == 0.0)
        assert_true(data.get('target') is None)

    def test_phash_partial_match(self):
        self._phash._validate = Mock(return_value=return_bytes('tests/images/netflix_match.png'))
        data = self._phash.classify('some url')
        assert_true(data.get('type') == 'PHISHING')
        assert_true(data.get('confidence') > 0.95 and data.get('confidence') < 1.0)
        assert_true(data.get('target') == 'netflix')
