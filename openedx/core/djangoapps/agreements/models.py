"""
Agreements models
"""

from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField

User = get_user_model()


class IntegritySignature(TimeStampedModel):
    """
    This model represents an integrity signature for a user + course combination.

    .. no_pii:
    """
    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    course_key = CourseKeyField(max_length=255, db_index=True)

    class Meta:
        app_label = 'agreements'
        unique_together = ('user', 'course_key')

class LTIPIISignature(models.Model):
    """
    This model stores a user's acknowledgement to share PII via LTI tools in a particular course.
    """
    course_key = CourseKeyField(max_length=255, db_index=True)
    user_id = models.IntegerField()
    lti_tools_hash = models.IntegerField()

    class Meta:
        app_label = 'agreements'
