"""
Survey Report models.
"""

from django.db import models
from jsonfield import JSONField

SURVEY_REPORT_PROCESSING = 'processing'
SURVEY_REPORT_GENERATED = 'generated'
SURVEY_REPORT_ERROR = 'error'

SURVEY_REPORT_STATES= [
    (SURVEY_REPORT_PROCESSING, 'Processing'),
    (SURVEY_REPORT_GENERATED, 'Generated'),
    (SURVEY_REPORT_ERROR, 'Error'),
]

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
    - state: State of the async generating process.
    """
    courses_offered = models.BigIntegerField(default=0, help_text="Total number of active unique courses.")
    learners = models.BigIntegerField(
        default=0,
        help_text="Total number of recently active users with login in some weeks."
    )
    registered_learners = models.BigIntegerField(
        default=0,
        help_text="Total number of users ever registered in the platform."
    )
    enrollments = models.BigIntegerField(default=0, help_text="Total number of active enrollments in the platform.")
    generated_certificates = models.BigIntegerField(default=0, help_text="Total number of generated certificates.")
    extra_data = JSONField(
        blank=True,
        default=dict,
        help_text="Extra information that will be saved in the report, E.g: site_name, openedx-release.",
    )
    created_at = models.DateTimeField(auto_now=True)
    state = models.CharField(
        max_length=24,
        choices=SURVEY_REPORT_STATES,
        default=SURVEY_REPORT_PROCESSING,
        help_text="State of the async generating process."
    )

    class Meta:
        ordering = ["-created_at"]
        get_latest_by = 'created_at'
