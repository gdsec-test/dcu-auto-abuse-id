import mongomock
import pymongo
import imagehash
import PIL
from nose.tools import assert_true, assert_false, assert_equal
from service.classifiers.phash import PHash
from settings import TestingConfig
from mock import patch, Mock
from dcdatabase.mongohelper import MongoHelper


def return_bytes(file_name):
    with open(file_name, mode='rb') as f:
        return (True, f.read())


class TestPhash:

    def setup(self):
        config = TestingConfig()
        self._phash = PHash(config)
        # Mock db
        self._phash._mongo._collection = mongomock.MongoClient().db.collection
        self._phash._mongo._collection.create_index([
            ('chunk1', pymongo.ASCENDING),
            ('chunk2', pymongo.ASCENDING),
            ('chunk3', pymongo.ASCENDING),
            ('chunk4', pymongo.ASCENDING)], unique=True)
        self._phash._mongo._collection.insert_many([{
            "target": "amazon",
            "chunk3": "62e2",
            "chunk2": "b023",
            "chunk1": "bf37",
            "type": "PHISHING",
            "chunk4": "62e2",
            "valid": "yes",
            "count": 100000
        }, {
            "target": "netflix",
            "chunk3": "2f00",
            "chunk2": "0585",
            "chunk1": "afbf",
            "type": "PHISHING",
            "chunk4": "8585",
            "valid": "yes",
            "count": 100000
        }, {
            "target": "amazon",
            "chunk3": "6ec4",
            "chunk2": "913b",
            "chunk1": "ae7b",
            "type": "PHISHING",
            "chunk4": "e0c0",
            "valid": "yes"
        }])

    def test_phash_classify_match(self):
        self._phash._validate = Mock(return_value=return_bytes('tests/images/phash_match.png'))
        data = self._phash.classify('some url')
        assert_equal(data.get('type'), 'PHISHING')
        assert_equal(round(data.get('confidence'), 4), 1.0)
        assert_equal(data.get('target'), 'amazon')

    def test_phash_classify_miss(self):
        self._phash._validate = Mock(return_value=return_bytes('tests/images/maaaaybe.jpg'))
        data = self._phash.classify('some url')
        assert_equal(data.get('type'), 'UNKNOWN')
        assert_equal(data.get('confidence'), 0.0)
        assert_equal(data.get('target'), None)

    def test_phash_classify_partial_match(self):
        self._phash._validate = Mock(return_value=return_bytes('tests/images/netflix_match.png'))
        data = self._phash.classify('some url')
        assert_equal(data.get('type'), 'PHISHING')
        assert_equal(round(data.get('confidence'), 4), 0.95)
        assert_equal(data.get('target'), 'netflix')

    @patch.object(MongoHelper, 'get_file')
    def test_phash_classify_image_id_match(self, mongo_get):
        mongo_get.return_value = return_bytes('tests/images/phash_match.png')
        data = self._phash.classify('some id', url=False)
        assert_equal(data.get('type'), 'PHISHING')
        assert_equal(round(data.get('confidence'), 4), 1.0)
        assert_equal(data.get('target'), 'amazon')

    @patch.object(MongoHelper, 'get_file')
    def test_phash_classify_image_id_miss(self, mongo_get):
        mongo_get.return_value = return_bytes('tests/images/maaaaybe.jpg')
        data = self._phash.classify('some id', url=False)
        assert_equal(data.get('type'), 'UNKNOWN')
        assert_equal(data.get('confidence'), 0.0)
        assert_equal(data.get('target'), None)

    @patch.object(MongoHelper, 'get_file')
    def test_phash_classify_image_id_partial_match(self, mongo_get):
        mongo_get.return_value = return_bytes('tests/images/netflix_match.png')
        data = self._phash.classify('some id', url=False)
        assert_equal(data.get('type'), 'PHISHING')
        assert_equal(round(data.get('confidence'), 4), 0.95)
        assert_equal(data.get('target'), 'netflix')

    @patch.object(MongoHelper, 'get_file')
    def test_phash_classify_image_id_missing_image(self, mongo_get):
        mongo_get.return_value = None
        data = self._phash.classify('some id', url=False)
        assert_equal(data.get('type'), 'UNKNOWN')
        assert_equal(data.get('confidence'), 0.0)
        assert_equal(data.get('target'), None)

    def test_add_classification_success(self):
        self._phash._mongo.get_file = Mock(return_value=('some file', 'some_bytes'))
        self._phash._get_image_hash = Mock(return_value='aaaabbbbccccdddd')
        iid = self._phash.add_classification('some image', 'PHISHING', 'amazon')
        assert_true(iid is not None)

    def test_add_classification_exists(self):
        self._phash._mongo.get_file = Mock(return_value=('blah', return_bytes('tests/images/phash_match.png')[1]))
        success, reason = self._phash.add_classification('some id', 'PHISHING', 'amazon')
        assert_false(success)
        assert_true(reason is not None)

    def test_add_classification_no_existing_image(self):
        success, reason = self._phash.add_classification('non-existant id', 'PHISHING', 'amazon')
        assert_false(success)
        assert_true(reason is not None)

    def test_phash_weigh_buckets(self):
        # Note: the values here differ slightly from the design doc at
        # https://confluence.godaddy.com/display/ITSecurity/Popularity+Weighting+for+Classified+Hashes
        # This is due to slight rounding differences, e.g. 5/6 ~= 0.833333333, etc.
        # When weighing, these values aren't rounded, resulting in slightly different values
        assert_equal(round(self._phash._weigh([0,0,0,0,1]),4), 0.7917)
        assert_equal(round(self._phash._weigh([0,0,0,0,5]),4), 0.875)
        assert_equal(round(self._phash._weigh([1,0,0,0,0]),4), 0.7583)
        assert_equal(round(self._phash._weigh([5,0,0,0,0]),4), 0.775)
        assert_equal(round(self._phash._weigh([0,0,12,263,13423]),4), 0.9989)
