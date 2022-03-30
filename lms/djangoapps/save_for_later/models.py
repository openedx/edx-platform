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
    marketing_url = models.CharField(max_length=255, null=True, blank=True)
    org_img_url = models.CharField(max_length=255, null=True, blank=True)
    weeks_to_complete = models.IntegerField(null=True)
    min_effort = models.IntegerField(null=True)
    max_effort = models.IntegerField(null=True)
    email_sent_count = models.IntegerField(null=True, default=0)
    reminder_email_sent = models.BooleanField(default=False, null=True)

    class Meta:
        unique_together = ('email', 'course_id',)

    def save(self, *args, **kwargs):
        self.email_sent_count = self.email_sent_count + 1
        super().save(*args, **kwargs)


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
    email_sent_count = models.IntegerField(null=True, default=0)
    reminder_email_sent = models.BooleanField(default=False, null=True)

    class Meta:
        unique_together = ('email', 'program_uuid',)

    def save(self, *args, **kwargs):
        self.email_sent_count = self.email_sent_count + 1
        super().save(*args, **kwargs)
