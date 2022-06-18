"""
Useful django models for implementing XBlock infrastructure in django.
If Django is unavailable, none of the classes below will work as intended.
"""
# pylint: disable=abstract-method
import logging
import warnings

try:
    from django.core.exceptions import ValidationError
    from django.db.models import CharField
    from django.db.models.lookups import IsNull
except ImportError:  # pragma: no cover
    # Django is unavailable, none of the classes below will work,
    # but we don't want the class definition to fail when interpreted.
    CharField = object
    IsNull = object

from opaque_keys.edx.keys import BlockTypeKey, CourseKey, LearningContextKey, UsageKey


log = logging.getLogger(__name__)


class _Creator:
    """
    DO NOT REUSE THIS CLASS. Provided for backwards compatibility only!

    A placeholder class that provides a way to set the attribute on the model.
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):  # pylint: disable=redefined-builtin
        if obj is None:
            return self  # pragma: no cover
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


# pylint: disable=missing-docstring,unused-argument
class CreatorMixin:
    """
    Mixin class to provide SubfieldBase functionality to django fields.
    See: https://docs.djangoproject.com/en/1.11/releases/1.8/#subfieldbase
    """

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super().contribute_to_class(cls, name, *args, **kwargs)
        setattr(cls, name, _Creator(self))

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)


def _strip_object(key):
    """
    Strips branch and version info if the given key supports those attributes.
    """
    if hasattr(key, 'version_agnostic') and hasattr(key, 'for_branch'):
        return key.for_branch(None).version_agnostic()
    return key


def _strip_value(value, lookup='exact'):
    """
    Helper function to remove the branch and version information from the given value,
    which could be a single object or a list.
    """
    if lookup == 'in':
        stripped_value = [_strip_object(el) for el in value]
    else:
        stripped_value = _strip_object(value)
    return stripped_value


# pylint: disable=logging-format-interpolation
class OpaqueKeyField(CreatorMixin, CharField):
    """
    A django field for storing OpaqueKeys.

    The baseclass will return the value from the database as a string, rather than an instance
    of an OpaqueKey, leaving the application to determine which key subtype to parse the string
    as.

    Subclasses must specify a KEY_CLASS attribute, in which case the field will use :meth:`from_string`
    to parse the key string, and will return an instance of KEY_CLASS.
    """
    description = "An OpaqueKey object, saved to the DB in the form of a string."

    Empty = object()
    KEY_CLASS = None

    def __init__(self, *args, **kwargs):
        if self.KEY_CLASS is None:
            raise ValueError('Must specify KEY_CLASS in OpaqueKeyField subclasses')

        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        error_message = f"{value} is not an instance of str or {self.KEY_CLASS}"
        assert isinstance(value, (str,) + (self.KEY_CLASS,)), error_message
        if value == '':
            # handle empty string for models being created w/o fields populated
            return None

        if isinstance(value, str):
            if value.endswith('\n'):
                # An opaque key with a trailing newline has leaked into the DB.
                # Log and strip the value.
                log.warning(
                    '%(db_table)s:%(name)s:%(key_class_name)s:to_python: '
                    'Invalid key: %(value)s. Removing trailing newline.',
                    {
                        'db_table': self.model._meta.db_table,  # pylint: disable=protected-access
                        'name': self.name,
                        'key_class_name': self.KEY_CLASS.__name__,
                        'value': repr(value),
                    }
                )
                value = value.rstrip()
            return self.KEY_CLASS.from_string(value)
        return value

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''  # CharFields should use '' as their empty value, rather than None

        if isinstance(value, str):
            value = self.KEY_CLASS.from_string(value)
        # pylint: disable=isinstance-second-argument-not-valid-type
        assert isinstance(value, self.KEY_CLASS), f"{value} is not an instance of {self.KEY_CLASS}"
        serialized_key = str(_strip_value(value))
        if serialized_key.endswith('\n'):
            # An opaque key object serialized to a string with a trailing newline.
            # Log the value - but do not modify it.
            log.warning(
                '%(db_table)s:%(name)s:%(key_class_name)s:get_prep_value: Invalid key: %(serialized_key)s.',
                {
                    'db_table': self.model._meta.db_table,  # pylint: disable=protected-access
                    'name': self.name,
                    'key_class_name': self.KEY_CLASS.__name__,
                    'serialized_key': repr(serialized_key),
                }
            )
        return serialized_key

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if self.blank or value is not self.Empty:
            return super().validate(value, model_instance)
        raise ValidationError(self.error_messages['blank'])

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return None

        return super().run_validators(value)


class OpaqueKeyFieldEmptyLookupIsNull(IsNull):
    """
    This overrides the default __isnull model filter to help enforce the special way
    we handle null / empty values in OpaqueKeyFields.
    """

    def get_prep_lookup(self):
        raise TypeError("Use this field's .Empty member rather than None or __isnull "
                        "to query for missing objects of this type.")


try:
    #  pylint: disable=no-member
    OpaqueKeyField.register_lookup(OpaqueKeyFieldEmptyLookupIsNull)
except AttributeError:
    #  Django was not imported
    pass


class LearningContextKeyField(OpaqueKeyField):
    """
    A django Field that stores a LearningContextKey object as a string.

    If you know for certain that your code will only deal with courses, use
    CourseKeyField instead, but if you are writing something more generic that
    could apply to any learning context (libraries, etc.), use this instead of
    CourseKeyField.
    """
    description = "A LearningContextKey object, saved to the DB in the form of a string"
    KEY_CLASS = LearningContextKey


class CourseKeyField(OpaqueKeyField):
    """
    A django Field that stores a CourseKey object as a string.
    """
    description = "A CourseKey object, saved to the DB in the form of a string"
    KEY_CLASS = CourseKey


class UsageKeyField(OpaqueKeyField):
    """
    A django Field that stores a UsageKey object as a string.
    """
    description = "A Location object, saved to the DB in the form of a string"
    KEY_CLASS = UsageKey


class LocationKeyField(UsageKeyField):
    """
    A django Field that stores a UsageKey object as a string.
    """

    def __init__(self, *args, **kwargs):
        warnings.warn("LocationKeyField is deprecated. Please use UsageKeyField instead.", stacklevel=2)
        super().__init__(*args, **kwargs)


class BlockTypeKeyField(OpaqueKeyField):
    """
    A django Field that stores a BlockTypeKey object as a string.
    """
    description = "A BlockTypeKey object, saved to the DB in the form of a string."
    KEY_CLASS = BlockTypeKey
