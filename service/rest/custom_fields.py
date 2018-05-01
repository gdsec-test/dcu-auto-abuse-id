import re

from flask_restplus.fields import Raw

URI_REGEX = re.compile(r'(http|https|ftp)://\S+\.\S+', flags=re.IGNORECASE)


class CustomField(Raw):
    """
    Custom Field base class with validate feature
    """
    __schema_type__ = 'string'

    def __init__(self, *args, **kwargs):
        super(CustomField, self).__init__(**kwargs)
        # custom params
        self.positive = kwargs.get('positive', True)

    def validate_empty(self):
        """
        Return when value is empty or null
        """
        if self.required:
            return False
        else:
            return True

    def validate(self, value):
        """
        Validate the value. return True if valid
        """
        pass


class Uri(CustomField):
    """
    URI (link) field
    """
    __schema_format__ = 'uri'
    __schema_example__ = 'http://website.com'

    def validate(self, value):
        if not value:
            return self.validate_empty()
        if not URI_REGEX.match(value):
            return False
        return True
