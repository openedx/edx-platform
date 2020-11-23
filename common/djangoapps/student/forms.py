"""
Utility functions for validating forms
"""


import re
from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.http import int_to_base36
from django.utils.translation import ugettext_lazy as _
from edx_ace import ace
from edx_ace.recipient import Recipient

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import get_current_site
from openedx.core.djangoapps.user_api import accounts as accounts_settings
from openedx.core.djangoapps.user_api.accounts.utils import is_secondary_email_feature_enabled
from openedx.core.djangoapps.user_authn.utils import should_redirect_to_logistration_mircrofrontend
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from common.djangoapps.student.message_types import AccountRecovery as AccountRecoveryMessage
from common.djangoapps.student.models import CourseEnrollmentAllowed, email_exists_or_retired


def send_account_recovery_email_for_user(user, request, email=None):
    """
    Send out a account recovery email for the given user.

    Arguments:
        user (User): Django User object
        request (HttpRequest): Django request object
        email (str): Send email to this address.
    """
    site = get_current_site()
    message_context = get_base_template_context(site)
    site_name = settings.LOGISTRATION_MICROFRONTEND_DOMAIN if should_redirect_to_logistration_mircrofrontend() \
        else configuration_helpers.get_value('SITE_NAME', settings.SITE_NAME)
    message_context.update({
        'request': request,  # Used by google_analytics_tracking_pixel
        'email': email,
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'reset_link': '{protocol}://{site}{link}?is_account_recovery=true'.format(
            protocol='https' if request.is_secure() else 'http',
            site=site_name,
            link=reverse('password_reset_confirm', kwargs={
                'uidb36': int_to_base36(user.id),
                'token': default_token_generator.make_token(user),
            }),
        )
    })

    msg = AccountRecoveryMessage().personalize(
        recipient=Recipient(user.username, email),
        language=get_user_preference(user, LANGUAGE_KEY),
        user_context=message_context,
    )
    ace.send(msg)
