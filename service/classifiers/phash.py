import logging
import pymongo
import imagehash
import io
from PIL import Image
from service.utils.urihelper import URIHelper
from interface import Classifier


class PHash(Classifier):

    CLASSIFICATION_DATA = dict(
        uri=None,
        type='UNKNOWN',
        confidence=0.0,
        target=None,
        method='pHash',
        meta=dict()
    )

    def __init__(self, settings):
        self._logger = logging.getLogger(__name__)
        self._client = pymongo.MongoClient(
            host=settings.DB_HOST, port=settings.DB_PORT, connect=False)
        self._db = self._client[settings.DB]
        self._collection = self._db[settings.COLLECTION]
        self._urihelper = URIHelper()

    def classify(self, url, confidence=0.75):
        valid, screenshot = self._validate(url)
        if not valid:
            return PHash.CLASSIFICATION_DATA
        hash_candidate = imagehash.phash(Image.open(io.BytesIO(screenshot)))
        res_doc = None
        max_certainty = confidence
        try:
            for doc in self._search(hash_candidate):
                doc_hash = imagehash.hex_to_hash(self._assemble_hash(doc))
                certainty = self._confidence(str(hash_candidate), str(doc_hash))
                self._logger.info('Found candidate image: {} with certainty {}'.format(doc.get('image'), certainty))
                if certainty >= max_certainty:
                    self._logger.info('Found new best candidate {} with {} certainty '.format(doc.get('image'), certainty))
                    max_certainty = certainty
                    res_doc = doc
                    if max_certainty == 1.0:
                        break
        except Exception as e:
            self._logger.error('Error classifying {} {}'.format(url, e))
        return self._create_response(res_doc, max_certainty)

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

    def _create_response(self, matching_doc, certainty):
        ret = PHash.CLASSIFICATION_DATA.copy()
        if matching_doc:
            matching_hash = self._assemble_hash(matching_doc)
            ret['type'] = matching_doc.get('type')
            ret['confidence'] = certainty
            ret['target'] = matching_doc.get('target')
            ret['meta']['imageId'] = matching_doc.get('image')
            ret['meta']['fingerprint'] = matching_hash
        return ret

    def _assemble_hash(self, doc):
        doc_hash = ''
        if doc:
            doc_hash = doc.get('chunk1') + doc.get('chunk2') + doc.get('chunk3') + doc.get('chunk4')
        return doc_hash

    def _validate(self, url):
        if not self._urihelper.resolves(url, timeout=3):
            self._logger.error('URL:{} does not resolve'.format(url))
            return (False, None)
        screenshot, _ = self._urihelper.get_site_data(url, timeout=3)
        if screenshot is None:
            self._logger.error('Unable to obtain screenshot for {}'.format(url))
            return (False, None)
        return (True, screenshot)

    def _confidence(self, hash1, hash2):
        return 1 - (self._phash_distance(hash1, hash2) / 64.0)

    def _phash_distance(self, hash1, hash2):
        return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')
