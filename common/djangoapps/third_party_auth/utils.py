"""
Common utilities for third_party_auth app.
"""

import json

from django.conf import settings
from django.core.exceptions import ValidationError
from social.backends.base import BaseAuth
from social.utils import module_member


# A dictionary of {name: class} entries for each python-social-auth backend available.
# Because this setting can specify arbitrary code to load and execute, it is set via
# normal Django settings only and cannot be changed at runtime:
def load_backend_classes(base_class=BaseAuth):
    """ Load the list of python-social-auth backend classes from Django settings """
    for class_path in settings.AUTHENTICATION_BACKENDS:
        auth_class = module_member(class_path)
        if issubclass(auth_class, base_class):
            yield auth_class


def clean_json(value, of_type):
    """ Simple helper method to parse and clean JSON """
    if not value.strip():
        return json.dumps(of_type())
    try:
        value_python = json.loads(value)
    except ValueError as err:
        raise ValidationError("Invalid JSON: {}".format(err.message))
    if not isinstance(value_python, of_type):
        raise ValidationError("Expected a JSON {}".format(of_type))
    return json.dumps(value_python, indent=4)
