from flask_restplus import abort, fields
from custom_fields import CustomField


def _error_abort(code, message):
    """Abstraction over restplus `abort`.
    Returns error with the status code and message.
    """
    error = {'code': code, 'message': message}
    abort(code, error=error)


def validate_payload(payload, api_model):
    """
    Validate payload against an api_model. Aborts in case of failure
    - This function is for custom fields as they can't be validated by
      flask restplus automatically.
    - This is to be called at the start of a post or put method
    """
    # check if any reqd fields are missing in payload
    for key in api_model:
        if api_model[key].required and key not in payload:
            _error_abort(400, 'Required field \'%s\' missing' % key)
    # check payload
    for key in payload:
        field = api_model[key]
        if isinstance(field, fields.List):
            field = field.container
            data = payload[key]
        else:
            data = [payload[key]]
        if isinstance(field, CustomField) and hasattr(field, 'validate'):
            for i in data:
                if not field.validate(i):
                    _error_abort(400, 'Validation of \'%s\' field failed' % key)
