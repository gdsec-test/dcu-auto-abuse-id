import abc


class Classifier(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def classify(self, url, confidence=0.75):
        """
        Attempt to classify the given url
        :param url:
        :param confidence: float indicating the minimum confidence for
        consideration (Default 75% confidence)
        :return: dictionary with at the following fields
        {
            "uri": string,
            "type": string,
            "confidence": float,
            "target": string,
            "method": string,
            "meta": {
                // Additional data (implimentation specific)
            }
        }
        """

    @abc.abstractmethod
    def add_classification(self, imageid, abuse_type, target=''):
        """
        Add an existing DCU image hash to the list of known hashes
        :param imageid: An existing DCU image identifier
        :param abuse_type: The type of the abuse associated with the image
        i.e. PHISHING MALWARE SPAM etc.
        :param target: The brand the abuse is targeting if applicable
        i.e. Netflix, Paypal etc.
        """
