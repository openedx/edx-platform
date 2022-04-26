"""
Provide django models to back the discussions app
"""
from __future__ import annotations

import logging
from enum import Enum
from collections import namedtuple

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_mysql.models import ListCharField
from jsonfield import JSONField
from lti_consumer.models import LtiConfiguration
from model_utils.models import TimeStampedModel
from opaque_keys.edx.django.models import LearningContextKeyField
from opaque_keys.edx.keys import CourseKey
from simple_history.models import HistoricalRecords

from openedx.core.djangoapps.config_model_utils.models import StackedConfigurationModel
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)

DEFAULT_PROVIDER_TYPE = 'legacy'
DEFAULT_CONFIG_ENABLED = True

ProviderExternalLinks = namedtuple(
    'ProviderExternalLinks',
    ['learn_more', 'configuration', 'general', 'accessibility', 'contact_email']
)

ProviderFeature = namedtuple('ProviderFeature', ['id', 'feature_support_type'])


class Features(Enum):
    """
    Features to be used/mapped in discussion providers
    """

    # Basic Supported Features
    PRIMARY_DISCUSSION_APP_EXPERIENCE = ProviderFeature('primary-discussion-app-experience', 'basic')
    LTI_BASIC_CONFIGURATION = ProviderFeature('lti-basic-configuration', 'basic')
    # DISCUSSION_PAGE = ProviderFeature('discussion-page', 'basic')

    # Partially Supported Features
    QUESTION_DISCUSSION_SUPPORT = ProviderFeature('question-discussion-support', 'partial')
    COMMUNITY_TA_SUPPORT = ProviderFeature('community-ta-support', 'partial')
    REPORT_FLAG_CONTENT_TO_MODERATORS = ProviderFeature('report/flag-content-to-moderators', 'partial')
    LTI_ADVANCED_SHARING_MODE = ProviderFeature('lti-advanced-sharing-mode', 'partial')
    AUTOMATIC_LEARNER_ENROLLMENT = ProviderFeature('automatic-learner-enrollment', 'partial')
    ANONYMOUS_POSTING = ProviderFeature('anonymous-posting', 'partial')
    INTERNATIONALIZATION_SUPPORT = ProviderFeature('internationalization-support', 'partial')
    EMAIL_NOTIFICATIONS = ProviderFeature('email-notifications', 'partial')
    WCAG_2_0_SUPPORT = ProviderFeature('wcag-2.0-support', 'partial')
    BLACKOUT_DISCUSSION_DATES = ProviderFeature('blackout-discussion-dates', 'partial')
    # WCAG_2_1 = ProviderFeature('wcag-2.1', 'partial')
    # EMBEDDED_COURSE_SECTIONS = ProviderFeature('embedded-course-sections', 'basic')

    # Fully Supported Features
    COURSE_COHORT_SUPPORT = ProviderFeature('course-cohort-support', 'full')
    RESEARCH_DATA_EVENTS = ProviderFeature('research-data-events', 'full')

    # Commonly Requested Features
    IN_PLATFORM_NOTIFICATIONS = ProviderFeature('in-platform-notifications', 'common')
    DISCUSSION_CONTENT_PROMPTS = ProviderFeature('discussion-content-prompts', 'common')
    GRADED_DISCUSSIONS = ProviderFeature('graded-discussions', 'common')
    DIRECT_MESSAGES_FROM_INSTRUCTORS = ProviderFeature('direct-messages-from-instructors', 'common')
    USER_MENTIONS = ProviderFeature('user-mentions', 'common')


def pii_sharing_required_message(provider_name):
    """
    Build an i18n'ed message stating PII sharing is required for the provider.
    """
    return _(
        '{provider} requires that LTI advanced sharing be enabled for your course,'
        ' as this provider uses email address and username to personalize'
        ' the experience. Please contact {support_contact} to enable this feature.'
    ).format(
        provider=provider_name,
        support_contact=(
            configuration_helpers.get_value(
                'CONTACT_EMAIL',
                getattr(settings, 'CONTACT_EMAIL', _('technical support'))
            )
        )
    )


AVAILABLE_PROVIDER_MAP = {
    'legacy': {
        'features': [
            Features.LTI_BASIC_CONFIGURATION.value.id,
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value.id,
            Features.QUESTION_DISCUSSION_SUPPORT.value.id,
            Features.COMMUNITY_TA_SUPPORT.value.id,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value.id,
            Features.AUTOMATIC_LEARNER_ENROLLMENT.value.id,
            Features.ANONYMOUS_POSTING.value.id,
            Features.INTERNATIONALIZATION_SUPPORT.value.id,
            Features.WCAG_2_0_SUPPORT.value.id,
            Features.BLACKOUT_DISCUSSION_DATES.value.id,
            Features.COURSE_COHORT_SUPPORT.value.id,
            Features.RESEARCH_DATA_EVENTS.value.id,
        ],
        'external_links': ProviderExternalLinks(
            learn_more='',
            configuration='',
            general='',
            accessibility='',
            contact_email='',
        )._asdict(),
        'messages': [],
        'has_full_support': True
    },
    'ed-discuss': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value.id,
            Features.LTI_BASIC_CONFIGURATION.value.id,
            Features.QUESTION_DISCUSSION_SUPPORT.value.id,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value.id,
            Features.LTI_ADVANCED_SHARING_MODE.value.id,
            Features.AUTOMATIC_LEARNER_ENROLLMENT.value.id,
            Features.ANONYMOUS_POSTING.value.id,
            Features.INTERNATIONALIZATION_SUPPORT.value.id,
            Features.EMAIL_NOTIFICATIONS.value.id,
            Features.WCAG_2_0_SUPPORT.value.id,
            Features.BLACKOUT_DISCUSSION_DATES.value.id,
            Features.IN_PLATFORM_NOTIFICATIONS.value.id,
            Features.USER_MENTIONS.value.id,
        ],
        'external_links': ProviderExternalLinks(
            learn_more='',
            configuration='',
            general='https://edstem.org/us/',
            accessibility='',
            contact_email='',
        )._asdict(),
        'messages': [],
        'has_full_support': False
    },
    'inscribe': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value.id,
            Features.LTI_BASIC_CONFIGURATION.value.id,
            Features.QUESTION_DISCUSSION_SUPPORT.value.id,
            Features.COMMUNITY_TA_SUPPORT.value.id,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value.id,
            Features.LTI_ADVANCED_SHARING_MODE.value.id,
            Features.AUTOMATIC_LEARNER_ENROLLMENT.value.id,
            Features.ANONYMOUS_POSTING.value.id,
            Features.INTERNATIONALIZATION_SUPPORT.value.id,
            Features.EMAIL_NOTIFICATIONS.value.id,
            Features.WCAG_2_0_SUPPORT.value.id,
            Features.RESEARCH_DATA_EVENTS.value.id,
            Features.IN_PLATFORM_NOTIFICATIONS.value.id,
            Features.DISCUSSION_CONTENT_PROMPTS.value.id,
        ],
        'external_links': ProviderExternalLinks(
            learn_more='',
            configuration='',
            general='https://www.inscribeapp.com/',
            accessibility='',
            contact_email='',
        )._asdict(),
        'messages': [pii_sharing_required_message('InScribe')],
        'has_full_support': False
    },
    'piazza': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value.id,
            Features.LTI_BASIC_CONFIGURATION.value.id,
            Features.QUESTION_DISCUSSION_SUPPORT.value.id,
            Features.COMMUNITY_TA_SUPPORT.value.id,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value.id,
            Features.LTI_ADVANCED_SHARING_MODE.value.id,
            Features.ANONYMOUS_POSTING.value.id,
            Features.EMAIL_NOTIFICATIONS.value.id,
            Features.WCAG_2_0_SUPPORT.value.id,
            Features.BLACKOUT_DISCUSSION_DATES.value.id,
        ],
        'external_links': ProviderExternalLinks(
            learn_more='https://piazza.com/product/overview',
            configuration='https://support.piazza.com/support/solutions/articles/48001065447-configure-piazza-within-edx',  # pylint: disable=line-too-long
            general='https://support.piazza.com/',
            accessibility='https://piazza.com/product/accessibility',
            contact_email='team@piazza.com',
        )._asdict(),
        'messages': [],
        'has_full_support': False
    },
    'yellowdig': {
        'features': [
            Features.PRIMARY_DISCUSSION_APP_EXPERIENCE.value.id,
            Features.LTI_BASIC_CONFIGURATION.value.id,
            Features.QUESTION_DISCUSSION_SUPPORT.value.id,
            Features.COMMUNITY_TA_SUPPORT.value.id,
            Features.REPORT_FLAG_CONTENT_TO_MODERATORS.value.id,
            Features.EMAIL_NOTIFICATIONS.value.id,
            Features.WCAG_2_0_SUPPORT.value.id,
            Features.RESEARCH_DATA_EVENTS.value.id,
            Features.IN_PLATFORM_NOTIFICATIONS.value.id,
            Features.GRADED_DISCUSSIONS.value.id,
            Features.DIRECT_MESSAGES_FROM_INSTRUCTORS.value.id,
            Features.USER_MENTIONS.value.id,
        ],
        'external_links': ProviderExternalLinks(
            learn_more='https://www.youtube.com/watch?v=ZACief-qMwY',
            configuration='',
            general='https://hubs.ly/H0J5Bn70',
            accessibility='',
            contact_email='learnmore@yellowdig.com',
        )._asdict(),
        'messages': [pii_sharing_required_message('Yellowdig')],
        'has_full_support': False,
        'admin_only_config': True,
    },
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
        Validate the model.
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
                enabled=DEFAULT_CONFIG_ENABLED,
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


class ProgramDiscussionsConfiguration(TimeStampedModel):
    """
    Associates a program with a discussion provider and configuration
    """

    program_uuid = models.CharField(
        primary_key=True,
        db_index=True,
        max_length=50,
        verbose_name=_("Program UUID"),
    )
    enabled = models.BooleanField(
        default=True,
        help_text=_("If disabled, the discussions in the associated program will be disabled.")
    )
    lti_configuration = models.ForeignKey(
        LtiConfiguration,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text=_("The LTI configuration data for this program/provider."),
    )
    provider_type = models.CharField(
        blank=False,
        max_length=50,
        verbose_name=_("Discussion provider"),
        help_text=_("The discussion provider's id"),
    )
    history = HistoricalRecords()

    def __str__(self):
        return f"Configuration(uuid='{self.program_uuid}', provider='{self.provider_type}', enabled={self.enabled})"

    @classmethod
    def is_enabled(cls, program_uuid) -> bool:
        """
        Check if there is an active configuration for a given program uuid

        Default to False, if no configuration exists
        """
        try:
            configuration = cls.objects.get(program_uuid=program_uuid)
            return configuration.enabled
        except cls.DoesNotExist:
            return False
