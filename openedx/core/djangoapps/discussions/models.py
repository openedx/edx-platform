"""
Provide django models to back the discussions app
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import LearningContextKeyField
from simple_history.models import HistoricalRecords

from lti_consumer.models import LtiConfiguration

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class DiscussionsConfiguration(TimeStampedModel):
    """
    Associates a learning context with discussion provider and configuration
    """

    context_key = LearningContextKeyField(
        primary_key=True,
        db_index=True,
        unique=True,
        max_length=255,
        # Translators: A key specifying a course, library, program, website, or some other collection of content where learning happens.
        verbose_name=_("Learning Context Key"),
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_("If disabled, the discussions in the associated learning context/course will be disabled.")
    )
    lti_configuration = models.ForeignKey(
        LtiConfiguration,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The LTI configuration data for this context/provider."),
    )
    plugin_configuration = JSONField(
        blank=True,
        default={},
        help_text=_("The plugin configuration data for this context/provider."),
    )
    provider_type = models.CharField(
        blank=False,
        max_length=100,
        verbose_name=_("Discussion provider"),
        help_text=_("The discussion tool/provider's id"),
    )
    history = HistoricalRecords()

    def clean(self):
        """
        Validate the model

        Currently, this only support courses, this can be extended
        whenever discussions are available in other contexts
        """
        if not CourseOverview.course_exists(self.context_key):
            raise ValidationError('Context Key should be an existing learning context.')

    def __str__(self):
        return "{context_key}: provider={provider} enabled={enabled}".format(
            context_key=self.context_key,
            provider=self.provider_type,
            enabled=self.enabled,
        )

    @classmethod
    def is_enabled(cls, context_key) -> bool:
        """
        Check if there is an active configuration for a given course key

        Default to False, if no configuration exists
        """
        configuration = cls.get(context_key)
        return configuration.enabled

    @classmethod
    def get(cls, context_key) -> cls:
        """
        Lookup a model by context_key
        """
        try:
            configuration = cls.objects.get(context_key=context_key)
        except cls.DoesNotExist:
            configuration = cls(context_key=context_key, enabled=False)
        return configuration
