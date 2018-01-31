import logging
import pymongo
import imagehash
import io
from PIL import Image
from service.utils.urihelper import URIHelper
from interface import Classifier


class PHash(Classifier):

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._client = pymongo.MongoClient(
            host=settings.DB_HOST, port=settings.DB_PORT)
        self._db = self._client[settings.DB]
        self._collection = self._db[settings.COLLECTION]
        self._urihelper = URIHelper()

    def classify(self, url, confidence=0.75):
        ret = dict(
            uri=url,
            type='UNKNOWN',
            confidence=0.0,
            target=None,
            method='pHash',
            meta=dict()
        )
        valid, screenshot = self._validate(url)
        if not valid:
            return ret
        hash_candidate = imagehash.phash(Image.open(io.BytesIO(screenshot)))
        res_doc = None
        max_certainty = confidence
        matching_hash = None
        for doc in self._search(hash_candidate):
            doc_hash = imagehash.hex_to_hash(doc['chunk1'] + doc['chunk2'] + doc['chunk3'] + doc['chunk4'])
            certainty = self._confidence(str(hash_candidate), str(doc_hash))
            self._logger.info('Found candidate image: {} with certainty {}'.format(doc.get('image'), certainty))
            if certainty >= max_certainty:
                self._logger.info('Found new best candidate {} with {} certainty '.format(doc.get('image'), certainty))
                max_certainty = certainty
                matching_hash = doc_hash
                res_doc = doc
        if res_doc is not None:
            ret['type'] = res_doc.get('type')
            ret['confidence'] = max_certainty
            ret['target'] = res_doc.get('target')
            ret['meta']['imageId'] = res_doc.get('image')
            ret['meta']['fingerprint'] = str(matching_hash)
        return ret

    def _search(self, hash):
        for doc in self._collection.find({
                '$or': [{
                    'chunk1': str(hash)[0:4]
                }, {
                    'chunk2': str(hash)[4:8]
                }, {
                    'chunk3': str(hash)[8:12]
                }, {
                    'chunk4': str(hash)[12:16]
                }]
        }):
            yield doc

    def _validate(self, url):
        if not self._urihelper.resolves(url, timeout=3):
            self._logger.error('URL:{} does not resolve'.format(url))
            return (False, None)
        screenshot, _ = self._urihelper.get_site_data(url, timeout=3)
        if screenshot is None:
            self._logger.error('Unable to obtain screenshot for {}'.format(url))
            return (False, None)
        return(True, screenshot)

    def _confidence(self, hash1, hash2):
        return 1 - (self._phash_distance(hash1, hash2) / 64.0)

    def _phash_distance(self, hash1, hash2):
        return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
