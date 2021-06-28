"""
Provide django models to back the discussions app
"""
from __future__ import annotations

import logging
from enum import Enum

from collections import namedtuple
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django_mysql.models import ListCharField
from jsonfield import JSONField
from lti_consumer.models import LtiConfiguration
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import LearningContextKeyField
from opaque_keys.edx.keys import CourseKey
from simple_history.models import HistoricalRecords

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger(__name__)

DEFAULT_PROVIDER_TYPE = 'legacy'


ProviderExternalLinks = namedtuple(
    'ProviderExternalLinks',
    ['learn_more', 'configuration', 'general', 'accessibility', 'contact_email']
)


class Features(Enum):
    """
    Features to be used/mapped in discussion providers
    """
    ANONYMOUS_POSTING = 'anonymous-posting'
    AUTOMATIC_LEARNER_ENROLLMENT = 'automatic-learner-enrollment'
    BLACKOUT_DISCUSSION_DATES = 'blackout-discussion-dates'
    COMMUNITY_TA_SUPPORT = 'community-ta-support'
    COURSE_COHORT_SUPPORT = 'course-cohort-support'
    DISCUSSION_PAGE = 'discussion-page'
    INTERNATIONALIZATION_SUPPORT = 'internationalization-support'
    PRIMARY_DISCUSSION_APP_EXPERIENCE = 'primary-discussion-app-experience'
    QUESTION_DISCUSSION_SUPPORT = 'question-discussion-support'
    REPORT_FLAG_CONTENT_TO_MODERATORS = 'report/flag-content-to-moderators'
    RESEARCH_DATA_EVENTS = 'research-data-events'
    WCAG_2_0_SUPPORT = 'wcag-2.0-support'
    WCAG_2_1 = 'wcag-2.1'
    ADVANCED_IN_CONTEXT_DISCUSSION = 'advanced-in-context-discussion'
    DIRECT_MESSAGES_FROM_INSTRUCTORS = 'direct-messages-from-instructors'
    DISCUSSION_CONTENT_PROMPTS = 'discussion-content-prompts'
    EMAIL_NOTIFICATIONS = 'email-notifications'
    EMBEDDED_COURSE_SECTIONS = 'embedded-course-sections'
    GRADED_DISCUSSIONS = 'graded-discussions'
    IN_PLATFORM_NOTIFICATIONS = 'in-platform-notifications'
    LTI_ADVANCED_SHARING_MODE = 'lti-advanced-sharing-mode'
    LTI_BASIC_CONFIGURATION = 'lti-basic-configuration'
    LTI = 'lti'
    SIMPLIFIED_IN_CONTEXT_DISCUSSION = 'simplified-in-context-discussion'
    USER_MENTIONS = 'user-mentions'


AVAILABLE_PROVIDER_MAP = {
    'legacy': {
        'features': [
            Features.DISCUSSION_PAGE.value,
            Features.WCAG_2_1.value,
            Features.AUTOMATIC_LEARNER_ENROLLMENT.value,
            Features.WCAG_2_0_SUPPORT.value,
            Features.INTERNATIONALIZATION_SUPPORT.value,
            Features.ANONYMOUS_POSTING.value,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value,
            Features.QUESTION_DISCUSSION_SUPPORT.value,
            Features.COMMUNITY_TA_SUPPORT.value,
            Features.BLACKOUT_DISCUSSION_DATES.value,
            Features.COURSE_COHORT_SUPPORT.value,
            Features.RESEARCH_DATA_EVENTS.value,
        ],
        'external_links': ProviderExternalLinks(
            '',
            '',
            '',
            '',
            '',
        )._asdict(),
    },
    'piazza': {
        'features': [
            Features.DISCUSSION_PAGE.value,
            Features.LTI.value,
            Features.WCAG_2_0_SUPPORT.value,
            Features.ANONYMOUS_POSTING.value,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value,
            Features.QUESTION_DISCUSSION_SUPPORT.value,
            Features.COMMUNITY_TA_SUPPORT.value,
            Features.EMAIL_NOTIFICATIONS.value,
            Features.BLACKOUT_DISCUSSION_DATES.value,
            Features.DISCUSSION_CONTENT_PROMPTS.value,
            Features.DIRECT_MESSAGES_FROM_INSTRUCTORS.value,
            Features.USER_MENTIONS.value,
        ],
        'external_links': ProviderExternalLinks(
            'https://piazza.com/product/overview',
            'https://support.piazza.com/support/solutions/articles/48001065447-configure-piazza-within-edx',
            'https://support.piazza.com/',
            'https://piazza.com/product/accessibility',
            'team@piazza.com',
        )._asdict()
    },
    'edx-next': {
        'features': [
            Features.AUTOMATIC_LEARNER_ENROLLMENT.value,
            Features.WCAG_2_0_SUPPORT.value,
            Features.INTERNATIONALIZATION_SUPPORT.value,
            Features.ANONYMOUS_POSTING.value,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value,
            Features.QUESTION_DISCUSSION_SUPPORT.value,
            Features.COMMUNITY_TA_SUPPORT.value,
            Features.EMAIL_NOTIFICATIONS.value,
            Features.BLACKOUT_DISCUSSION_DATES.value,
            Features.SIMPLIFIED_IN_CONTEXT_DISCUSSION.value,
            Features.ADVANCED_IN_CONTEXT_DISCUSSION.value,
            Features.COURSE_COHORT_SUPPORT.value,
            Features.RESEARCH_DATA_EVENTS.value,
            Features.DISCUSSION_CONTENT_PROMPTS.value,
            Features.GRADED_DISCUSSIONS.value,
        ],
        'external_links': ProviderExternalLinks(
            '',
            '',
            '',
            '',
            '',
        )._asdict(),
    },
    'yellowdig': {
        'features': [
            Features.WCAG_2_0_SUPPORT.value,
            Features.ANONYMOUS_POSTING.value,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value,
            Features.QUESTION_DISCUSSION_SUPPORT.value,
            Features.COMMUNITY_TA_SUPPORT.value,
            Features.EMAIL_NOTIFICATIONS.value,
            Features.RESEARCH_DATA_EVENTS.value,
            Features.IN_PLATFORM_NOTIFICATIONS.value,
            Features.GRADED_DISCUSSIONS.value,
            Features.DIRECT_MESSAGES_FROM_INSTRUCTORS.value,
            Features.USER_MENTIONS.value,
        ],
        'external_links': ProviderExternalLinks(
            'https://www.youtube.com/watch?v=ZACief-qMwY',
            '',
            'https://hubs.ly/H0J5Bn7',
            '',
            'learnmore@yellowdig.com',
        )._asdict(),
    },
    'inscribe': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value,
            Features.LTI_BASIC_CONFIGURATION.value,
        ],
        'external_links': ProviderExternalLinks(
            '',
            '',
            'https://www.inscribeapp.com/',
            '',
            '',
        )._asdict(),
    },
    'discourse': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value,
            Features.LTI_BASIC_CONFIGURATION.value,
            Features.LTI_ADVANCED_SHARING_MODE.value,
        ],
        'external_links': ProviderExternalLinks(
            '',
            '',
            'http://discourse.org/',
            '',
            '',
        )._asdict(),
    },
    'ed-discuss': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value,
            Features.LTI_BASIC_CONFIGURATION.value,
            Features.WCAG_2_0_SUPPORT.value,
            Features.INTERNATIONALIZATION_SUPPORT.value,
            Features.ANONYMOUS_POSTING.value,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value,
            Features.QUESTION_DISCUSSION_SUPPORT.value,
            Features.COMMUNITY_TA_SUPPORT.value,
            Features.EMAIL_NOTIFICATIONS.value,
        ],
        'external_links': ProviderExternalLinks(
            '',
            '',
            'https://edstem.org/us/',
            '',
            '',
        )._asdict(),
    }
}


def get_supported_providers() -> list[str]:
    """
    Return the list of supported discussion providers

    TODO: Load this from entry points?
    """
    providers = [
        'legacy',
        'piazza',
    ]
    return providers


class ProviderFilter(StackedConfigurationModel):
    """
    Associate allow/deny-lists of discussions providers with courses/orgs
    """

    allow = ListCharField(
        base_field=models.CharField(
            choices=[
                (provider, provider)
                for provider in get_supported_providers()
            ],
            max_length=20,
        ),
        blank=True,
        help_text=_("Comma-separated list of providers to allow, eg: {choices}").format(
            choices=','.join(get_supported_providers()),
        ),
        # max_length = (size * (max_length + len(','))
        # max_length = (   3 * (        20 +       1))
        max_length=63,
        # size = len(get_supported_providers())
        size=3,
        verbose_name=_('Allow List'),
    )
    deny = ListCharField(
        base_field=models.CharField(
            choices=[
                (provider, provider)
                for provider in get_supported_providers()
            ],
            max_length=20,
        ),
        blank=True,
        help_text=_("Comma-separated list of providers to deny, eg: {choices}").format(
            choices=','.join(get_supported_providers()),
        ),
        # max_length = (size * (max_length + len(','))
        # max_length = (   3 * (        20 +       1))
        max_length=63,
        # size = len(get_supported_providers())
        size=3,
        verbose_name=_('Deny List'),
    )

    STACKABLE_FIELDS = (
        'enabled',
        'allow',
        'deny',
    )

    def __str__(self):
        return 'ProviderFilter(org="{org}", course="{course}", allow={allow}, deny={deny})'.format(
            allow=self.allow,
            course=self.course or '',
            deny=self.deny,
            org=self.org or '',
        )

    @property
    def available_providers(self) -> list[str]:
        """
        Return a filtered list of available providers
        """
        _providers = get_supported_providers()
        if self.allow:
            _providers = [
                provider
                for provider in _providers
                if provider in self.allow
            ]
        if self.deny:
            _providers = [
                provider
                for provider in _providers
                if provider not in self.deny
            ]
        return _providers

    @classmethod
    def get_available_providers(cls, course_key: CourseKey) -> list[str]:
        _filter = cls.current(course_key=course_key)
        providers = _filter.available_providers
        return providers


class DiscussionsConfiguration(TimeStampedModel):
    """
    Associates a learning context with discussion provider and configuration
    """

    context_key = LearningContextKeyField(
        primary_key=True,
        db_index=True,
        unique=True,
        max_length=255,
        # Translators: A key specifying a course, library, program,
        # website, or some other collection of content where learning
        # happens.
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
        return "DiscussionsConfiguration(context_key='{context_key}', provider='{provider}', enabled={enabled})".format(
            context_key=self.context_key,
            provider=self.provider_type,
            enabled=self.enabled,
        )

    def supports(self, feature: str) -> bool:
        """
        Check if the provider supports some feature
        """
        features = AVAILABLE_PROVIDER_MAP.get(self.provider_type)['features'] or []
        has_support = bool(feature in features)
        return has_support

    @classmethod
    def is_enabled(cls, context_key: CourseKey) -> bool:
        """
        Check if there is an active configuration for a given course key

        Default to False, if no configuration exists
        """
        configuration = cls.get(context_key)
        return configuration.enabled

    # pylint: disable=undefined-variable
    @classmethod
    def get(cls, context_key: CourseKey) -> cls:
        """
        Lookup a model by context_key
        """
        try:
            configuration = cls.objects.get(context_key=context_key)
        except cls.DoesNotExist:
            configuration = cls(
                context_key=context_key,
                enabled=False,
                provider_type=DEFAULT_PROVIDER_TYPE,
            )
        return configuration

    # pylint: enable=undefined-variable

    @property
    def available_providers(self) -> list[str]:
        return ProviderFilter.current(course_key=self.context_key).available_providers

    @classmethod
    def get_available_providers(cls, context_key: CourseKey) -> list[str]:
        return ProviderFilter.current(course_key=context_key).available_providers
