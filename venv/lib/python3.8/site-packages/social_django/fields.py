import json
import warnings

from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils.encoding import force_str

from social_core.utils import setting_name


POSTGRES_JSONFIELD = getattr(settings, setting_name('POSTGRES_JSONFIELD'),
                             False)

if POSTGRES_JSONFIELD:
    warnings.warn(
        'SOCIAL_AUTH_POSTGRES_JSONFIELD has been renamed to '
        'SOCIAL_AUTH_JSONFIELD_ENABLED and will be removed in the next release.'
    )
    JSONFIELD_ENABLED = True
else:
    JSONFIELD_ENABLED = getattr(settings, setting_name('JSONFIELD_ENABLED'),
                                False)

if JSONFIELD_ENABLED:
    JSONFIELD_CUSTOM = getattr(settings, setting_name('JSONFIELD_CUSTOM'), None)

    if JSONFIELD_CUSTOM is not None:
        try:
            from django.utils.module_loading import import_string
        except ImportError:
            from importlib import import_module as import_string
        JSONFieldBase = import_string(JSONFIELD_CUSTOM)
    else:
        try:
            from django.db.models import JSONField as JSONFieldBase
        except ImportError:
            from django.contrib.postgres.fields import \
                JSONField as JSONFieldBase
else:
    JSONFieldBase = models.TextField


class JSONField(JSONFieldBase):
    """Simple JSON field that stores python structures as JSON strings
    on database.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, *args, **kwargs):
        return self.to_python(value)

    def to_python(self, value):
        """
        Convert the input JSON value into python structures, raises
        django.core.exceptions.ValidationError if the data can't be converted.
        """
        if self.blank and not value:
            return {}
        value = value or '{}'
        if isinstance(value, bytes):
            value = str(value, 'utf-8')
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception as err:
                raise ValidationError(str(err))
        else:
            return value

    def validate(self, value, model_instance):
        """Check value is a valid JSON string, raise ValidationError on
        error."""
        if isinstance(value, str):
            super().validate(value, model_instance)
            try:
                json.loads(value)
            except Exception as err:
                raise ValidationError(str(err))

    def get_prep_value(self, value):
        """Convert value to JSON string before save"""
        try:
            return json.dumps(value)
        except Exception as err:
            raise ValidationError(str(err))

    def value_to_string(self, obj):
        """Return value from object converted to string properly"""
        return force_str(self.value_from_object(obj))

    def value_from_object(self, obj):
        """Return value dumped to string."""
        orig_val = super().value_from_object(obj)
        return self.get_prep_value(orig_val)
