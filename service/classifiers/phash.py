import logging
import io
import imagehash

from PIL import Image
from service.utils.urihelper import URIHelper
from service.classifiers.interface import Classifier
from dcdatabase.mongohelper import MongoHelper


class PHash(Classifier):

    def __init__(self, settings):
        """
        Constructor
        :param settings:
        """
        self._logger = logging.getLogger(__name__)
        self._mongo = MongoHelper(settings)
        self._urihelper = URIHelper()
        self._bucket_ranges = settings.BUCKETS
        self._bucket_weights = settings.BUCKET_WEIGHTS

    def classify(self, candidate, url=True, confidence=0.75):
        """
        Intake method to classify a provided candidate with an optional confidence
        :param candidate:
        :param url: True if the candidate is a url else candidate is treated as a DCU Image ID
        :param confidence: not used for phash classifer
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
        return self._classify_image_id(candidate) if not url else self._classify_uri(candidate)

    def _classify_uri(self, uri):
        valid, screenshot = self._validate(uri)
        if not valid:
            ret_dict = PHash._get_response_dict()
            ret_dict['candidate'] = uri
            return ret_dict
        hash_candidate = self._get_image_hash(io.BytesIO(screenshot))
        doc, certainty = self._find_match(hash_candidate)
        return PHash._create_response(uri, doc, certainty)

    def _classify_image_id(self, imageid):
        image = None
        try:
            _, image = self._mongo.get_file(imageid)
        except Exception as e:
            self._logger.error('Unable to find image {}'.format(imageid))
        image_hash = self._get_image_hash(io.BytesIO(image))
        doc, certainty = self._find_match(image_hash)
        return PHash._create_response(imageid, doc, certainty)

    def _find_match(self, hash_candidate):
        res_dict = None
        # array of buckets for determining confidence
        confidence_buckets = [ 0 ] * len(self._bucket_weights)
        # dict of bucket arrays for determining confidence of each possible target
        target_buckets = {}
        # dict of bucket arrays for determining confidence of each possible abuse type
        type_buckets = {}

        target_match = {
            'value': 'UNKNOWN',
            'confidence': 0.0
        }
        type_match = {
            'value': 'UNKNOWN',
            'confidence': 0.0
        }

        if not hash_candidate:
            return (None, None)

        for doc in self._search(hash_candidate):
            try:
                doc_hash = imagehash.hex_to_hash(PHash._assemble_hash(doc))
            except Exception as e:
                self._logger.error('Error assembling hash for {}'.format(doc.get('_id')))
                continue
            if doc.get('valid') not in ['yes', True]:
                continue # Don't consider hashes marked as "invalid"
            doctype = doc.get('type', 'UNKNOWN')
            doctarget = doc.get('target', 'UNKNOWN')
            if doctype not in type_buckets.keys():
                type_buckets[doctype] = [ 0 ] * len(self._bucket_weights)
            if doctarget not in target_buckets.keys():
                target_buckets[doctarget] = [ 0 ] * len(self._bucket_weights)

            certainty = ( PHash._confidence(str(hash_candidate), str(doc_hash)) * 100 )
            for i in range(0, len(confidence_buckets)):
                if self._bucket_ranges[i] < certainty and certainty <= self._bucket_ranges[i+1]:
                    count = doc.get('count', 1)
                    confidence_buckets[i] += count
                    type_buckets[doctype][i] += count
                    target_buckets[doctarget][i] += count

        match_confidence = self._weigh(confidence_buckets)
        if match_confidence == 0:
            return (None, None)

        # Based on weighted averages, find out what the "most likely target" is among matching hashes
        for target in target_buckets.keys():
            target_confidence = self._weigh(target_buckets[target])
            if target_confidence > target_match['confidence']:
                target_match = {
                    'value': target,
                    'confidence': target_confidence
                }

        # Based on weighted averages, find out what the "most likely abuse type" is among matching hashes
        for type_val in type_buckets.keys():
            type_confidence = self._weigh(type_buckets[type_val])
            if type_confidence > type_match['confidence']:
                type_match = {
                    'value': type_val,
                    'confidence': type_confidence
                }
                
        res_dict = {
            'target': target_match['value'],
            'type': type_match['value']
        }
        return res_dict, match_confidence

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
        if self._mongo.add_incident(
            {
                'valid': 'yes',
                'type': abuse_type,
                'target': target,
                'chunk1': str(image_hash)[0:4],
                'chunk2': str(image_hash)[4:8],
                'chunk3': str(image_hash)[8:12],
                'chunk4': str(image_hash)[12:16]
            }
        ):
            return True, ''
        else:
            return False, 'No new document created for {}'.format(imageid)

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

    def _weigh(self, buckets):
        confidence_over = 0.0
        confidence_under = float(len(self._bucket_weights))

        for i in range(0, len(buckets)):
            confidence_over += buckets[i] * self._bucket_weights[i]
            confidence_under += buckets[i]
        if confidence_over == 0:
            return 0

        confidence = ((confidence_over / confidence_under) * len(self._bucket_weights)) + self._bucket_ranges[0]
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
