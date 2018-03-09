import logging
import io
import imagehash
import math

from PIL import Image
from service.utils.urihelper import URIHelper
from service.classifiers.interface import Classifier
from dcdatabase.mongohelper import MongoHelper
from pymongo import ReturnDocument
from bson.objectid import ObjectId
from collections import defaultdict

class PHash(Classifier):

    def __init__(self, settings):
        """
        Constructor
        :param settings:
        """
        self._logger = logging.getLogger(__name__)
        self._mongo = MongoHelper(settings)
        self._urihelper = URIHelper()
        self._bucket_weights = settings.BUCKET_WEIGHTS
        self._num_buckets = len(settings.BUCKET_WEIGHTS)

    def classify(self, candidate, url=True, confidence=0.75):
        """
        Intake method to classify a provided candidate with an optional confidence
        :param candidate:
        :param url: True if the candidate is a url else candidate is treated as a DCU Image ID
        :param confidence: a minimum confidence value that must be between 0.75 and 1.0 (inclusive)
        :return: dictionary with at the following fields
        {
            "candidate": string,
            "type": string,
            "confidence": float,
            "target": string,
            "method": string,
            "meta": {
                // Additional data (implementation specific)
            }
        }
        """
        if (confidence <= 0.75):
            confidence = 0.75
        if (confidence >= 1.0):
            confidence = 1.0

        return self._classify_image_id(candidate, confidence) if not url else self._classify_uri(candidate, confidence)

    def _classify_uri(self, uri, confidence):
        valid, screenshot = self._validate(uri)
        if not valid:
            ret_dict = PHash._get_response_dict()
            ret_dict['candidate'] = uri
            return ret_dict
        hash_candidate = self._get_image_hash(io.BytesIO(screenshot))
        doc, certainty = self._find_match(hash_candidate, confidence)
        return PHash._create_response(uri, doc, certainty)

    def _classify_image_id(self, imageid, confidence):
        image = None
        try:
            _, image = self._mongo.get_file(imageid)
        except Exception as e:
            self._logger.error('Unable to find image {}'.format(imageid))
        image_hash = self._get_image_hash(io.BytesIO(image))
        doc, certainty = self._find_match(image_hash, confidence)
        return PHash._create_response(imageid, doc, certainty)

    def _find_match(self, hash_candidate, min_confidence):
        '''
        Takes a hash, and provides a confidence rating + type/target based on
        similar hashes, and how many times those similar hashes have been flagged,
        using weighted averages to make the determination
        :param hash_candidate: string of the phash to search for
        :return Tuple: dict of type/target, and confidence rating
        '''
        if not hash_candidate:
            return (None, None)
        # Initialize bucket sets for confidence, possible targets, and abuse types
        # allowing for multiple buckets based on malicious type
        # i.e.: target_buckets['anything'] becomes e.g. [0, 0, 0, 0, 0] default
        confidence_buckets = [0] * self._num_buckets
        target_buckets = defaultdict(lambda: [0] * self._num_buckets)
        type_buckets = defaultdict(lambda: [0] * self._num_buckets)
        min_confidence *= 100
        bucket_step = (100.0-min_confidence) / self._num_buckets
        for doc in self._search(hash_candidate):
            try:
                doc_hash = imagehash.hex_to_hash(PHash._assemble_hash(doc))
            except Exception as e:
                self._logger.error('Error assembling hash for {}'.format(doc.get('_id')))
                continue

            certainty = PHash._confidence(str(hash_candidate), str(doc_hash)) * 100
            if certainty <= min_confidence and min_confidence != 100.0:
                continue
            # calculate the index for the appropriate bucket
            # e.g. 76.0 yields 0, 80 yields 1, 100 yields 4 (assuming bucket_step is 5 and min_confidence is 75)
            bucket = 0
            if min_confidence != 100.0:
                bucket = int(math.ceil((certainty-min_confidence)/bucket_step))-1
            count = doc.get('count', 1)
            confidence_buckets[bucket] += count
            type_buckets[doc.get('type', 'UNKNOWN')][bucket] += count
            target_buckets[doc.get('target', 'UNKNOWN')][bucket] += count

        if min_confidence == 100.0:
            match_confidence = 1.0 if confidence_buckets[0] else 0.0
        else:
            match_confidence = self._weigh(confidence_buckets, min_confidence)
                
        res_dict = {
            'target': self._best_bucket(target_buckets, min_confidence),
            'type': self._best_bucket(type_buckets, min_confidence)
        }
        return (res_dict, match_confidence) if match_confidence else (None, None)

    def _best_bucket(self, buckets, min_confidence):
        '''
        Takes a dict of buckets, weighs them, and returns the key for the highest-weighed bucket
        :param buckets: A dict of buckets
        :return String: the key for the highest-confidence bucket
        '''
        best_confidence = 0.0
        match = 'UNKNOWN'
        for key, value in buckets.iteritems():
            confidence = self._weigh(value, min_confidence)
            if confidence > best_confidence:
                match = key
                best_confidence = confidence
        return match

    def add_classification(self, imageid, abuse_type, target=''):
        '''
        Hashes a given DCU image and adds it to the fingerprints collection
        :param imageid: Existing BSON image id
        :param abuse_type: Type of abuse associated with image
        :param target: Brand abuse is targeting if applicable
        :return Tuple: Boolean indicating success and a message
        Example:
        Invalid image id given
        (False, 'Unable to locate image xyz')
        Error trying to hash image
        (False, 'Unable to hash image xyz')
        A new document was inserted
        (True, '')
        A new document was not created. This can be for several reasons.
        Most likely a document with the same hash already exists
        (False, 'No new document created for xyz')
        '''
        image = None
        try:
            _, image = self._mongo.get_file(imageid)
        except Exception as e:
            return False, 'Unable to locate image {}'.format(imageid)
        image_hash = self._get_image_hash(io.BytesIO(image))
        if not image_hash:
            return False, 'Unable to hash image {}'.format(imageid)

        if self._mongo._collection.find_one_and_update(
            {
                'chunk1': str(image_hash)[0:4],
                'chunk2': str(image_hash)[4:8],
                'chunk3': str(image_hash)[8:12],
                'chunk4': str(image_hash)[12:16]
            },
            {
                '$inc': { 'count': 1 },
                '$setOnInsert': {
                    'valid': 'yes',
                    'type': abuse_type,
                    'target': target,
                    'imageid': ObjectId(imageid)
                }
            },
            upsert = True,
            return_document = ReturnDocument.AFTER
        ):
            return True, ''
        return False, 'Unable to add or update DB for {}'.format(imageid)

    def _search(self, hash_val):
        """
        Pymongo search clause to find a match based on extracted 16bit chunks
        :param hash_val:
        :return:
        """
        for doc in self._mongo.find_incidents(
            {'valid': 'yes',
             '$or': [{
                'chunk1': str(hash_val)[0:4]
             }, {
                'chunk2': str(hash_val)[4:8]
             }, {
                'chunk3': str(hash_val)[8:12]
             }, {
                'chunk4': str(hash_val)[12:16]
             }]}
        ):
            yield doc

    def _weigh(self, buckets, min_confidence):
        confidence_over = 0.0
        confidence_under = float(self._num_buckets)

        for i in range(0, len(buckets)):
            confidence_over += buckets[i] * self._bucket_weights[i]
            confidence_under += buckets[i]
        if confidence_over == 0:
            return 0

        confidence = ((confidence_over / confidence_under) * self._num_buckets) + min_confidence
        return (confidence / 100.0)

    @staticmethod
    def _create_response(candidate, matching_doc, certainty):
        """
        Assembles the response dictionary returned to caller
        :param matching_doc:
        :param certainty:
        :return dictionary:
        """
        ret = PHash._get_response_dict()
        ret['candidate'] = candidate
        if matching_doc:
            ret['type'] = matching_doc['type']
            ret['confidence'] = certainty
            ret['target'] = matching_doc['target']
        return ret

    @staticmethod
    def _assemble_hash(doc):
        """
        Reassembles all of the separate chunks back into the original hash but as a string
        :param doc:
        :return string:
        """
        doc_hash = ''
        if doc:
            doc_hash = doc.get('chunk1') + doc.get('chunk2') + doc.get('chunk3') + doc.get('chunk4')
        return doc_hash

    def _validate(self, url):
        """
        Attempts to extract and return a screenshot of a provided url
        :param url:
        :return:
        """
        if not self._urihelper.resolves(url, timeout=5):
            self._logger.error('URL:{} does not resolve'.format(url))
            return (False, None)
        screenshot, _ = self._urihelper.get_site_data(url, timeout=10)
        if screenshot is None:
            self._logger.error('Unable to obtain screenshot for {}'.format(url))
            return (False, None)
        return (True, screenshot)

    @staticmethod
    def _confidence(hash1, hash2):
        """
        Calculate the percentage of like bits by subtracting the number
        of positions that differ from the total number of bits
        :param hash1:
        :param hash2:
        :return:
        """
        return 1 - (PHash._phash_distance(hash1, hash2) / 64.0)

    @staticmethod
    def _phash_distance(hash1, hash2):
        """
        Count the number of bit positions that differ between the two
        hashes
        :param hash1:
        :param hash2:
        :return:
        """
        return bin(int(hash1, 16) ^ int(hash2, 16)).count('1')

    @staticmethod
    def _get_response_dict():
        return dict(
            candidate=None,
            type='UNKNOWN',
            confidence=0.0,
            target=None,
            method='pHash',
            meta=dict())

    def _get_image_hash(self, ifile):
        '''
        Fetches a perceptual hash of the given file like object
        :param ifile: File like object representing an image
        :return: ImageHash object or None
        '''
        try:
            with Image.open(ifile) as image:
                return imagehash.phash(image)
        except Exception as e:
            self._logger.error('Unable to hash image {}'.format(e))
