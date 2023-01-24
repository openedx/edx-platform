"""
Survey Report models.
"""

from django.db import models
from jsonfield import JSONField


class SurveyReport(models.Model):
    """
    This model stores information to automate the way of gathering impact data from the openedx project.

    .. no_pii:

    fields:
    - courses_offered: Total number of active unique courses.
    - learner: Recently active users with login in some weeks.
    - registered_learners: Total number of users ever registered in the platform.
    - enrollments: Total number of active enrollments in the platform.
    - generated_certificates: Total number of generated certificates.
    - extra_data: Extra information that will be saved in the report, E.g: site_name, openedx-release.
    """
    courses_offered = models.BigIntegerField(help_text="Total number of active unique courses.")
    learners = models.BigIntegerField(help_text="Total number of recently active users with login in some weeks.")
    registered_learners = models.BigIntegerField(help_text="Total number of users ever registered in the platform.")
    enrollments = models.BigIntegerField(help_text="Total number of active enrollments in the platform.")
    generated_certificates = models.BigIntegerField(help_text="Total number of generated certificates.")
    extra_data = JSONField(
        blank=True,
        default=dict,
        help_text="Extra information that will be saved in the report, E.g: site_name, openedx-release.",
    )
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = 'created_at'
