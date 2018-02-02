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
