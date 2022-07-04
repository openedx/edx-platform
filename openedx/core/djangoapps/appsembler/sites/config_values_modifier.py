"""
Tahoe: Configuration modifiers for Tahoe.
"""

from urllib.parse import urlsplit
from logging import getLogger

from django.conf import settings

log = getLogger(__name__)


class TahoeConfigurationValueModifier:
    """
    Calculate URL values for Tahoe.

    This is useful to reduce the cost of changing a Site domain.
    """

    FIELD_OVERRIDERS = {
        'SITE_NAME': 'get_site_name',
        'LMS_ROOT_URL': 'get_lms_root_url',
        'ACTIVATION_EMAIL_SUPPORT_LINK': 'get_activation_email_support_link',
        'PASSWORD_RESET_SUPPORT_LINK': 'get_password_reset_support_link',
        'css_overrides_file': 'get_css_overrides_file',
    }

    def __init__(self, site_config_instance):
        self.site_config_instance = site_config_instance

    def normalize_get_value_params(self, name, default):
        """
        Amend the name and default values for Tahoe.

        This resolves few quirks and tech-debt in Open edX in which some variables don't exist while others exists
        in multiple spellings/cases.
        """
        # Tahoe: Default value is needed for this
        if name == 'LANGUAGE_CODE' and default is None:
            # TODO: Ask Dashboard 2.0 / AMC to set the `LANGUAGE_CODE` by default.
            default = 'en'

        if name == 'PLATFORM_NAME':
            # Always use the lower case so the configuration is easier to maintain.
            name = 'platform_name'

        return name, default

    def get_domain(self):
        domain = None
        if hasattr(self.site_config_instance, 'site'):
            domain = self.site_config_instance.site.domain

        return domain

    def get_site_name(self):
        return self.get_domain()

    def get_css_overrides_file(self):
        return self.site_config_instance.get_css_overrides_file()

    def get_lms_root_url(self):
        """
        Provide override for LMS_ROOT_URL synced with `SITE_NAME`.
        """
        # We cannot simply use a protocol-relative URL for LMS_ROOT_URL
        # This is because the URL here will be used by such activities as
        # sending activation links to new users. The activation link needs the
        # scheme address verification emails. The callers using this variable
        # expect the scheme in the URL
        return '{scheme}://{domain}'.format(
            scheme=urlsplit(settings.LMS_ROOT_URL).scheme,
            domain=self.get_domain(),
        )

    def get_activation_email_support_link(self):
        """
        RED-2471: Use Multi-tenant `/help` URL for password reset emails.
        """
        return '{root_url}/help'.format(root_url=self.get_lms_root_url())

    def get_password_reset_support_link(self):
        """
        RED-2385: Use Multi-tenant `/help` URL for activation emails.
        """
        return '{root_url}/help'.format(root_url=self.get_lms_root_url())

    def override_value(self, name):
        """
        Given a value name, return a hard-coded default completely disregarding the stored values.

        This is useful to simplify the domain name change for Sites.

        :return (should_override, overridden_value)
        """
        value_getter_method_name = self.FIELD_OVERRIDERS.get(name)
        if value_getter_method_name:
            if self.get_domain():
                value_getter = getattr(self, value_getter_method_name)
                return True, value_getter()
        return False, None


def init_configuration_modifier_for_site_config(sender, instance, **kwargs):
    instance.tahoe_config_modifier = TahoeConfigurationValueModifier(site_config_instance=instance)
