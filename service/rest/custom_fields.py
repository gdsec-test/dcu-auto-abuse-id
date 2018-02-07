import re
from flask_restplus.fields import Raw

URI_REGEX = re.compile(r'(http|https|ftp)://\S+\.\S+')


class CustomField(Raw):
    """
    Custom Field base class with validate feature
    """
    __schema_type__ = 'string'

    def __init__(self, *args, **kwargs):
        super(CustomField, self).__init__(**kwargs)
        # custom params
        self.positive = kwargs.get('positive', True)

    def format(self, value):
        """
        format the text in database for output
        works only for GET requests
        """
        if not self.validate(value):
            print 'Validation of field with value \"%s\" (%s) failed' % (
                value, str(self.__class__.__name__))
            # raise MarshallingError
            # disabling for development purposes as the server crashes when
            # exception is raised. can be enabled when the project is mature
        if self.__schema_type__ == 'string':
            return unicode(value)
        else:
            return value

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
