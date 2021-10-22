"""
Django ORM models for save_for_later APP
"""


from model_utils.models import TimeStampedModel
from django.db import models
from opaque_keys.edx.django.models import CourseKeyField


class SavedCourse(TimeStampedModel):
    user_id = models.IntegerField(null=True, blank=True)
    email = models.EmailField(db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)


class SavedProgram(TimeStampedModel):
    user_id = models.IntegerField(null=True, blank=True)
    email = models.EmailField(db_index=True)
    program_uuid = models.UUIDField()
