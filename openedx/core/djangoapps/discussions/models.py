from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import LearningContextKeyField
from organizations.models import Organization
from simple_history.models import HistoricalRecords

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class DiscussionProviderConfig(TimeStampedModel):
    """
    Configuration model to store configuration for Discussions applications.
    """

    name = models.CharField(
        blank=False,
        max_length=100,
        help_text=_("A user-friendly name for this configuration. e.g. SomeOrg Discourse")
    )
    provider = models.CharField(
        blank=False,
        db_index=True,
        max_length=100,
        verbose_name=_("Discussion provider"),
        help_text=_("The discussion tool/provider."),
    )
    config = JSONField(
        blank=True,
        default={},
        help_text=_("The configuration data for this provider."),
    )
    restrict_to_site = models.ForeignKey(
        to=Site,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Optionally restrict this config for use only on this site."),
        db_index=True,
    )
    restrict_to_org = models.ForeignKey(
        to=Organization,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        help_text=_("Optionally restrict this config for use only on this Organization."),
        db_index=True,
    )

    history = HistoricalRecords()

    def clean(self):
        if self.restrict_to_org and self.restrict_to_site:
            raise ValidationError("Can only set one form of restriction, site or org.")

    def __str__(self):
        return "{name} provider={provider} restricted to [site={site} org={org}]".format(
            provider=self.provider,
            name=self.name,
            site=self.restrict_to_site,
            org=self.restrict_to_org
        )


class LearningContextDiscussionConfig(TimeStampedModel):
    """
    Associates a learning context with a :class:`DiscussionProviderConfig`.

    Also allows overriding some configuration on a course-by-course basis.
    """

    context_key = LearningContextKeyField(
        primary_key=True,
        db_index=True,
        unique=True,
        max_length=255,
        verbose_name=_("Learning Context"),
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_("If disabled, the discussions in the associated learning context/course will be disabled.")
    )
    provider_config = models.ForeignKey(
        to=DiscussionProviderConfig,
        null=True,
        blank=True,
        help_text=_("The configuration to use for this learning context."),
        on_delete=models.SET_NULL,
    )
    config_overrides = JSONField(
        blank=True,
        default={},
        help_text=_("Overrides course-specific configuration."),
    )

    history = HistoricalRecords()

    def clean(self):
        # Currently, this only support courses, this can be extended whenever discussions
        # are available in other contexts
        if not CourseOverview.course_exists(self.context_key):
            raise ValidationError('Context Key should be an existing learning context.')

    def __str__(self):
        return '{context_key}: enabled={enabled} config="{config}" has_overrides={has_overrides}'.format(
            context_key=self.context_key,
            enabled=self.enabled,
            config=self.provider_config and self.provider_config.name,
            has_overrides=bool(self.config_overrides),
        )
