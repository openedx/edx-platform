"""
Django ORM models for save_for_later APP
"""


from model_utils.models import TimeStampedModel
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField

from openedx.core.djangolib.model_mixins import DeletableByUserValue


class SavedCourse(DeletableByUserValue, TimeStampedModel):
    """
    Tracks save course by email.

    .. pii: Stores email address of the User.
    .. pii_types: email_address
    .. pii_retirement: local_api
    """
    user_id = models.IntegerField(null=True, blank=True)
    email = models.EmailField(db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)


class SavedProgram(DeletableByUserValue, TimeStampedModel):
    """
    Tracks save program by email.

    .. pii: Stores email address of the User.
    .. pii_types: email_address
    .. pii_retirement: local_api
    """
    user_id = models.IntegerField(null=True, blank=True)
    email = models.EmailField(db_index=True)
    program_uuid = models.UUIDField()
