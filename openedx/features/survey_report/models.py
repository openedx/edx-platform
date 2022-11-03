"""
Survey Report models.
"""

from django.db import models
from jsonfield import JSONField


class SurveyReport(models.Model):
    """
    This model stores information to automate the way of gathering impact data from the openedx project.

    .. no_pii:
    """
    courses_offered = models.BigIntegerField()
    learners = models.BigIntegerField()
    registered_learners = models.BigIntegerField()
    enrollments = models.BigIntegerField()
    generated_certificates = models.BigIntegerField()
    extra_data = JSONField(
        blank=True,
        default=dict,
        help_text="Extra information for instance data",
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = 'created_at'
