from django.db import models
from django.core.exceptions import ValidationError
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import Locator

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^xmodule_django\.models\.CourseKeyField"])
add_introspection_rules([], ["^xmodule_django\.models\.LocationKeyField"])


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

    def get_query_set(self):
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


class CourseKeyField(models.CharField):
    description = "A SlashSeparatedCourseKey object, saved to the DB in the form of a string"

    __metaclass__ = models.SubfieldBase

    Empty = object()

    def to_python(self, value):
        if value is self.Empty or value is None:
            return None

        assert isinstance(value, (basestring, CourseKey))
        if value == '':
            # handle empty string for models being created w/o fields populated
            return None

        if isinstance(value, basestring):
            return SlashSeparatedCourseKey.from_deprecated_string(value)
        else:
            return value

    def get_prep_lookup(self, lookup, value):
        if lookup == 'isnull':
            raise TypeError('Use CourseKeyField.Empty rather than None to query for a missing CourseKeyField')

        return super(CourseKeyField, self).get_prep_lookup(
            lookup,
            # strip key before comparing
            _strip_value(value, lookup)
        )

    def get_prep_value(self, value):
        if value is self.Empty or value is None:
            return ''  # CharFields should use '' as their empty value, rather than None

        assert isinstance(value, CourseKey)
        return unicode(_strip_value(value))

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if not self.blank and value is self.Empty:
            raise ValidationError(self.error_messages['blank'])
        else:
            return super(CourseKeyField, self).validate(value, model_instance)

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return

        return super(CourseKeyField, self).run_validators(value)


class LocationKeyField(models.CharField):
    description = "A Location object, saved to the DB in the form of a string"

    __metaclass__ = models.SubfieldBase

    Empty = object()

    def to_python(self, value):
        if value is self.Empty or value is None:
            return value

        assert isinstance(value, (basestring, UsageKey))

        if value == '':
            return None

        if isinstance(value, basestring):
            return Location.from_deprecated_string(value)
        else:
            return value

    def get_prep_lookup(self, lookup, value):
        if lookup == 'isnull':
            raise TypeError('Use LocationKeyField.Empty rather than None to query for a missing LocationKeyField')

        # remove version and branch info before comparing keys
        return super(LocationKeyField, self).get_prep_lookup(
            lookup,
            # strip key before comparing
            _strip_value(value, lookup)
        )

    def get_prep_value(self, value):
        if value is self.Empty:
            return ''

        assert isinstance(value, UsageKey)
        return unicode(_strip_value(value))

    def validate(self, value, model_instance):
        """Validate Empty values, otherwise defer to the parent"""
        # raise validation error if the use of this field says it can't be blank but it is
        if not self.blank and value is self.Empty:
            raise ValidationError(self.error_messages['blank'])
        else:
            return super(LocationKeyField, self).validate(value, model_instance)

    def run_validators(self, value):
        """Validate Empty values, otherwise defer to the parent"""
        if value is self.Empty:
            return

        return super(LocationKeyField, self).run_validators(value)
