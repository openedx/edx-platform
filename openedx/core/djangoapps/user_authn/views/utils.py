"""
User Auth Views Utils
"""
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext as _
from ipware.ip import get_client_ip

from common.djangoapps import third_party_auth
from common.djangoapps.third_party_auth import pipeline
from common.djangoapps.third_party_auth.models import clean_username
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip

API_V1 = 'v1'
UUID4_REGEX = '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}'
ENTERPRISE_ENROLLMENT_URL_REGEX = fr'/enterprise/{UUID4_REGEX}/course/{settings.COURSE_KEY_REGEX}/enroll'


def third_party_auth_context(request, redirect_to, tpa_hint=None):
    """
    Context for third party auth providers and the currently running pipeline.

    Arguments:
        request (HttpRequest): The request, used to determine if a pipeline
            is currently running.
        redirect_to: The URL to send the user to following successful
            authentication.
        tpa_hint (string): An override flag that will return a matching provider
            as long as its configuration has been enabled

    Returns:
        dict

    """
    context = {
        "currentProvider": None,
        "platformName": configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        "providers": [],
        "secondaryProviders": [],
        "finishAuthUrl": None,
        "errorMessage": None,
        "registerFormSubmitButtonText": _("Create Account"),
        "syncLearnerProfileData": False,
        "pipeline_user_details": {}
    }

    if third_party_auth.is_enabled():
        for enabled in third_party_auth.provider.Registry.displayed_for_login(tpa_hint=tpa_hint):
            info = {
                "id": enabled.provider_id,
                "name": enabled.name,
                "iconClass": enabled.icon_class or None,
                "iconImage": enabled.icon_image.url if enabled.icon_image else None,
                "skipHintedLogin": enabled.skip_hinted_login_dialog,
                "loginUrl": pipeline.get_login_url(
                    enabled.provider_id,
                    pipeline.AUTH_ENTRY_LOGIN,
                    redirect_url=redirect_to,
                ),
                "registerUrl": pipeline.get_login_url(
                    enabled.provider_id,
                    pipeline.AUTH_ENTRY_REGISTER,
                    redirect_url=redirect_to,
                ),
            }
            context["providers" if not enabled.secondary else "secondaryProviders"].append(info)

        running_pipeline = pipeline.get(request)
        if running_pipeline is not None:
            current_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)
            user_details = running_pipeline['kwargs']['details']
            if user_details:
                username = running_pipeline['kwargs'].get('username') or user_details.get('username')
                if username:
                    user_details['username'] = clean_username(username)
                context['pipeline_user_details'] = user_details

            if current_provider is not None:
                context["currentProvider"] = current_provider.name
                context["finishAuthUrl"] = pipeline.get_complete_url(current_provider.backend_name)
                context["syncLearnerProfileData"] = current_provider.sync_learner_profile_data

                if current_provider.skip_registration_form:
                    # As a reliable way of "skipping" the registration form, we just submit it automatically
                    context["autoSubmitRegForm"] = True

        # Check for any error messages we may want to display:
        for msg in messages.get_messages(request):
            if msg.extra_tags.split()[0] == "social-auth":
                # msg may or may not be translated. Try translating [again] in case we are able to:
                context["errorMessage"] = _(str(msg))  # pylint: disable=E7610
                break

    return context


def get_mfe_context(request, redirect_to, tpa_hint=None):
    """
    Returns Authn MFE context.
    """

    ip_address = get_client_ip(request)[0]
    country_code = country_code_from_ip(ip_address)
    context = third_party_auth_context(request, redirect_to, tpa_hint)
    context.update({
        'countryCode': country_code,
    })
    return context
