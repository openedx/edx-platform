"""
Useful django models for implementing XBlock infrastructure in django.
"""
import warnings
import logging

from django.db import models
from django.core.exceptions import ValidationError
from opaque_keys.edx.keys import CourseKey, UsageKey, BlockTypeKey

log = logging.getLogger(__name__)


class NoneToEmptyManager(models.Manager):
    """
    A :class:`django.db.models.Manager` that has a :class:`NoneToEmptyQuerySet`
    as its `QuerySet`, initialized with a set of specified `field_names`.
    """
    def __init__(self):
        """
        Args:
            field_names: The list of field names to initialize the :class:`NoneToEmptyQuerySet` with.
        """
        super(NoneToEmptyManager, self).__init__()

    def get_queryset(self):
        """
        Returns the result of NoneToEmptyQuerySet instead of a regular QuerySet.
        """
        return NoneToEmptyQuerySet(self.model, using=self._db)


class NoneToEmptyQuerySet(models.query.QuerySet):
    """
    A :class:`django.db.query.QuerySet` that replaces `None` values passed to `filter` and `exclude`
    with the corresponding `Empty` value for all fields with an `Empty` attribute.

    This is to work around Django automatically converting `exact` queries for `None` into
    `isnull` queries before the field has a chance to convert them to queries for it's own
    empty value.
    """
    def _filter_or_exclude(self, *args, **kwargs):
        for name in self.model._meta.get_all_field_names():
            field_object, _model, direct, _m2m = self.model._meta.get_field_by_name(name)
            if direct and hasattr(field_object, 'Empty'):
                for suffix in ('', '_exact'):
                    key = '{}{}'.format(name, suffix)
                    if key in kwargs and kwargs[key] is None:
                        kwargs[key] = field_object.Empty
        return super(NoneToEmptyQuerySet, self)._filter_or_exclude(*args, **kwargs)


def _strip_object(key):
    """
    Strips branch and version info if the given key supports those attributes.
    """
    if hasattr(key, 'version_agnostic') and hasattr(key, 'for_branch'):
        return key.for_branch(None).version_agnostic()
    else:
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


class OpaqueKeyField(models.CharField):
    """
    A django field for storing OpaqueKeys.

    The baseclass will return the value from the database as a string, rather than an instance
    of an OpaqueKey, leaving the application to determine which key subtype to parse the string
    as.

    Subclasses must specify a KEY_CLASS attribute, in which case the field will use :meth:`from_string`
    to parse the key string, and will return an instance of KEY_CLASS.
    """
    description = "An OpaqueKey object, saved to the DB in the form of a string."

    __metaclass__ = models.SubfieldBase

    Empty = object()
    KEY_CLASS = None

    def __init__(self, *args, **kwargs):
        if self.KEY_CLASS is None:
            raise ValueError('Must specify KEY_CLASS in OpaqueKeyField subclasses')

        super(OpaqueKeyField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        assert isinstance(value, (basestring, self.KEY_CLASS)), \
            "%s is not an instance of basestring or %s" % (value, self.KEY_CLASS)
        if value == '':
            # handle empty string for models being created w/o fields populated
            return None

        if isinstance(value, basestring):
            if value.endswith('\n'):
                # An opaque key with a trailing newline has leaked into the DB.
                # Log and strip the value.
                log.warning('{}:{}:{}:to_python: Invalid key: {}. Removing trailing newline.'.format(
                    self.model._meta.db_table,
                    self.name,
                    self.KEY_CLASS.__name__,
                    repr(value)
                ))
                value = value.rstrip()
            return self.KEY_CLASS.from_string(value)
        else:
            return value

    def get_prep_lookup(self, lookup, value):
        if lookup == 'isnull':
            raise TypeError('Use {0}.Empty rather than None to query for a missing {0}'.format(self.__class__.__name__))

        return super(OpaqueKeyField, self).get_prep_lookup(
            lookup,
            # strip key before comparing
            _strip_value(value, lookup)
        )

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''  # CharFields should use '' as their empty value, rather than None

        assert isinstance(value, self.KEY_CLASS), "%s is not an instance of %s" % (value, self.KEY_CLASS)
        serialized_key = unicode(_strip_value(value))
        if serialized_key.endswith('\n'):
            # An opaque key object serialized to a string with a trailing newline.
            # Log the value - but do not modify it.
            log.warning('{}:{}:{}:get_prep_value: Invalid key: {}.'.format(
                self.model._meta.db_table,
                self.name,
                self.KEY_CLASS.__name__,
                repr(serialized_key)
            ))
        return serialized_key

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if not self.blank and value is self.Empty:
            raise ValidationError(self.error_messages['blank'])
        else:
            return super(OpaqueKeyField, self).validate(value, model_instance)

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return

        return super(OpaqueKeyField, self).run_validators(value)


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
        super(LocationKeyField, self).__init__(*args, **kwargs)


class BlockTypeKeyField(OpaqueKeyField):
    """
    A django Field that stores a BlockTypeKey object as a string.
    """
    description = "A BlockTypeKey object, saved to the DB in the form of a string."
    KEY_CLASS = BlockTypeKey
