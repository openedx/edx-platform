"""
Models course live integrations.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from lti_consumer.models import LtiConfiguration
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import CourseKeyField
from simple_history.models import HistoricalRecords


class CourseLiveConfiguration(TimeStampedModel):
    """
    Associates a Course with a LTI provider and configuration
    """
    course_key = CourseKeyField(max_length=255, db_index=True, null=False)
    enabled = models.BooleanField(
        default=True,
        help_text=_("If disabled, the LTI in the associated course will be disabled.")
    )
    lti_configuration = models.ForeignKey(
        LtiConfiguration,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The LTI configuration data for this course/provider."),
    )
    provider_type = models.CharField(
        blank=False,
        max_length=50,
        verbose_name=_("LTI provider"),
        help_text=_("The LTI provider's id"),
    )
    free_tier = models.BooleanField(
        default=False,
        help_text=_("True, if LTI credential are provided by Org globally")
    )
    history = HistoricalRecords()

    def __str__(self):
        return f"Configuration(course_key='{self.course_key}', provider='{self.provider_type}', enabled={self.enabled})"

    @classmethod
    def is_enabled(cls, course_key) -> bool:
        """
        Check if there is an active configuration for a given course key

        Default to False, if no configuration exists
        """
        configuration = cls.get(course_key)
        if not configuration:
            return False
        return configuration.enabled

    @classmethod
    def get(cls, course_key):
        """
        Lookup a course live configuration by course uuid.
        """
        return cls.objects.filter(
            course_key=course_key
        ).first()
