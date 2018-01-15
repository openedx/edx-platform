"""
Useful django models for implementing XBlock infrastructure in django.
"""
import logging

from django.db import models

# Re-exporting imports moved to edx-opaque-keys
# pylint: disable=unused-import
from opaque_keys.edx.fields import (
    BlockTypeKeyField,
    CourseKeyField,
    LocationKeyField,
    UsageKeyField,
)
# pylint: enable=unused-import

from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


class NoneToEmptyManager(models.Manager):
    """
    A :class:`django.db.models.Manager` that has a :class:`NoneToEmptyQuerySet`
    as its `QuerySet`, initialized with a set of specified `field_names`.
    """
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
        # pylint: disable=protected-access
        for field_object in self.model._meta.get_fields():
            direct = not field_object.auto_created or field_object.concrete
            if direct and hasattr(field_object, 'Empty'):
                for suffix in ('', '_exact'):
                    key = '{}{}'.format(field_object.name, suffix)
                    if key in kwargs and kwargs[key] is None:
                        kwargs[key] = field_object.Empty

        return super(NoneToEmptyQuerySet, self)._filter_or_exclude(*args, **kwargs)


class UsageKeyWithRunField(UsageKeyField):
    """
    Subclass of UsageKeyField that automatically fills in
    missing `run` values, for old Mongo courses.
    """
    def to_python(self, value):
        value = super(UsageKeyWithRunField, self).to_python(value)
        if value is not None and value.run is None:
            value = value.replace(course_key=modulestore().fill_in_run(value.course_key))
        return value
