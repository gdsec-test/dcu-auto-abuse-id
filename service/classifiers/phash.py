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

    def classify(self, candidate, url=True, confidence=0.75):
        """
        Intake method to classify a provided candidate with an optional confidence
        :param candidate:
        :param url: True if the candidate is a url else candidate is treated as a DCU Image ID
        :param confidence: float indicating the minimum confidence for
        consideration (Default 75% confidence)
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

    def _classify_image_id(self, imageid, confidence=0.75):
        image = None
        try:
            _, image = self._mongo.get_file(imageid)
        except Exception as e:
            self._logger.error('Unable to find image {}'.format(imageid))
        image_hash = self._get_image_hash(io.BytesIO(image))
        doc, certainty = self._find_match(image_hash, confidence)
        return PHash._create_response(imageid, doc, certainty)

    def _find_match(self, hash_candidate, confidence):
        res_doc = None
        max_certainty = confidence
        if hash_candidate:
            for doc in self._search(hash_candidate):
                try:
                    doc_hash = imagehash.hex_to_hash(PHash._assemble_hash(doc))
                except Exception as e:
                    self._logger.error('Error assembling hash for {}'.format(doc.get('_id')))
                    continue
                certainty = PHash._confidence(str(hash_candidate), str(doc_hash))
                self._logger.info('Found candidate image: {} with certainty {}'.format(doc.get('image'), certainty))
                if certainty >= max_certainty:
                    self._logger.info('Found new best candidate {} with {} certainty '.format(doc.get('image'), certainty))
                    max_certainty = certainty
                    res_doc = doc
                    if max_certainty == 1.0:
                        break
        return (res_doc, max_certainty) if res_doc else (None, None)

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
            matching_hash = PHash._assemble_hash(matching_doc)
            ret['type'] = matching_doc.get('type')
            ret['confidence'] = certainty
            ret['target'] = matching_doc.get('target')
            ret['meta']['imageId'] = str(matching_doc.get('imageId'))
            ret['meta']['fingerprint'] = matching_hash
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
