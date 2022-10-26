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
    courses_offered = models.IntegerField()
    learners = models.IntegerField()
    registered_learners = models.IntegerField()
    enrollments = models.IntegerField()
    generated_certificates = models.IntegerField()
    extra_data = JSONField(
        blank=True,
        default={},
        help_text="Extra information for instance data",
    )
    request_details = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = 'created_at'
