""" Login related views """

import json
import logging

import urlparse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.user_authn.views.deprecated import (
    register_user as old_register_view, signin_user as old_login_view
)
from openedx.core.djangoapps.external_auth.login_and_register import login as external_auth_login
from openedx.core.djangoapps.external_auth.login_and_register import register as external_auth_register
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import is_request_in_themed_site
from openedx.core.djangoapps.user_api.accounts.utils import is_secondary_email_feature_enabled
from openedx.core.djangoapps.user_api.api import (
    RegistrationFormFactory,
    get_account_recovery_form,
    get_login_session_form,
    get_password_reset_form,
)
from openedx.core.djangoapps.user_authn.cookies import are_logged_in_cookies_set
from openedx.features.enterprise_support.api import enterprise_customer_for_request
from openedx.features.enterprise_support.utils import (
    handle_enterprise_cookies_for_logistration,
    update_logistration_context_for_enterprise,
)
from student.helpers import get_next_url_for_login_page
import third_party_auth
from third_party_auth import pipeline
from third_party_auth.decorators import xframe_allow_whitelisted


log = logging.getLogger(__name__)


@require_http_methods(['GET'])
@ensure_csrf_cookie
@xframe_allow_whitelisted
def login_and_registration_form(request, initial_mode="login"):
    """Render the combined login/registration form, defaulting to login

    This relies on the JS to asynchronously load the actual form from
    the user_api.

    Keyword Args:
        initial_mode (string): Either "login" or "register".

    """
    # Determine the URL to redirect to following login/registration/third_party_auth
    redirect_to = get_next_url_for_login_page(request)

    # If we're already logged in, redirect to the dashboard
    # Note: We check for the existence of login-related cookies in addition to is_authenticated
    #  since Django's SessionAuthentication middleware auto-updates session cookies but not
    #  the other login-related cookies. See ARCH-282.
    if request.user.is_authenticated and are_logged_in_cookies_set(request):
        return redirect(redirect_to)

    # Retrieve the form descriptions from the user API
    form_descriptions = _get_form_descriptions(request)

    # Our ?next= URL may itself contain a parameter 'tpa_hint=x' that we need to check.
    # If present, we display a login page focused on third-party auth with that provider.
    third_party_auth_hint = None
    if '?' in redirect_to:
        try:
            next_args = urlparse.parse_qs(urlparse.urlparse(redirect_to).query)
            provider_id = next_args['tpa_hint'][0]
            tpa_hint_provider = third_party_auth.provider.Registry.get(provider_id=provider_id)
            if tpa_hint_provider:
                if tpa_hint_provider.skip_hinted_login_dialog:
                    # Forward the user directly to the provider's login URL when the provider is configured
                    # to skip the dialog.
                    if initial_mode == "register":
                        auth_entry = pipeline.AUTH_ENTRY_REGISTER
                    else:
                        auth_entry = pipeline.AUTH_ENTRY_LOGIN
                    return redirect(
                        pipeline.get_login_url(provider_id, auth_entry, redirect_url=redirect_to)
                    )
                third_party_auth_hint = provider_id
                initial_mode = "hinted_login"
        except (KeyError, ValueError, IndexError) as ex:
            log.exception("Unknown tpa_hint provider: %s", ex)

    # We are defaulting to true because all themes should now be using the newer page.
    if is_request_in_themed_site() and not configuration_helpers.get_value('ENABLE_COMBINED_LOGIN_REGISTRATION', True):
        if initial_mode == "login":
            return old_login_view(request)
        elif initial_mode == "register":
            return old_register_view(request)

    # Allow external auth to intercept and handle the request
    ext_auth_response = _external_auth_intercept(request, initial_mode)
    if ext_auth_response is not None:
        return ext_auth_response

    # Account activation message
    account_activation_messages = [
        {
            'message': message.message, 'tags': message.tags
        } for message in messages.get_messages(request) if 'account-activation' in message.tags
    ]

    account_recovery_messages = [
        {
            'message': message.message, 'tags': message.tags
        } for message in messages.get_messages(request) if 'account-recovery' in message.tags
    ]

    # Otherwise, render the combined login/registration page
    context = {
        'data': {
            'login_redirect_url': redirect_to,
            'initial_mode': initial_mode,
            'third_party_auth': _third_party_auth_context(request, redirect_to, third_party_auth_hint),
            'third_party_auth_hint': third_party_auth_hint or '',
            'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            'support_link': configuration_helpers.get_value('SUPPORT_SITE_LINK', settings.SUPPORT_SITE_LINK),
            'password_reset_support_link': configuration_helpers.get_value(
                'PASSWORD_RESET_SUPPORT_LINK', settings.PASSWORD_RESET_SUPPORT_LINK
            ) or settings.SUPPORT_SITE_LINK,
            'account_activation_messages': account_activation_messages,
            'account_recovery_messages': account_recovery_messages,

            # Include form descriptions retrieved from the user API.
            # We could have the JS client make these requests directly,
            # but we include them in the initial page load to avoid
            # the additional round-trip to the server.
            'login_form_desc': json.loads(form_descriptions['login']),
            'registration_form_desc': json.loads(form_descriptions['registration']),
            'password_reset_form_desc': json.loads(form_descriptions['password_reset']),
            'account_recovery_form_desc': json.loads(form_descriptions['account_recovery']),
            'account_creation_allowed': configuration_helpers.get_value(
                'ALLOW_PUBLIC_ACCOUNT_CREATION', settings.FEATURES.get('ALLOW_PUBLIC_ACCOUNT_CREATION', True)),
            'is_account_recovery_feature_enabled': is_secondary_email_feature_enabled()
        },
        'login_redirect_url': redirect_to,  # This gets added to the query string of the "Sign In" button in header
        'responsive': True,
        'allow_iframing': True,
        'disable_courseware_js': True,
        'combined_login_and_register': True,
        'disable_footer': not configuration_helpers.get_value(
            'ENABLE_COMBINED_LOGIN_REGISTRATION_FOOTER',
            settings.FEATURES['ENABLE_COMBINED_LOGIN_REGISTRATION_FOOTER']
        ),
    }

    enterprise_customer = enterprise_customer_for_request(request)
    update_logistration_context_for_enterprise(request, context, enterprise_customer)

    response = render_to_response('student_account/login_and_register.html', context)
    handle_enterprise_cookies_for_logistration(request, response, context)

    return response


def _get_form_descriptions(request):
    """Retrieve form descriptions from the user API.

    Arguments:
        request (HttpRequest): The original request, used to retrieve session info.

    Returns:
        dict: Keys are 'login', 'registration', and 'password_reset';
            values are the JSON-serialized form descriptions.

    """

    return {
        'password_reset': get_password_reset_form().to_json(),
        'account_recovery': get_account_recovery_form().to_json(),
        'login': get_login_session_form(request).to_json(),
        'registration': RegistrationFormFactory().get_registration_form(request).to_json()
    }


def _third_party_auth_context(request, redirect_to, tpa_hint=None):
    """Context for third party auth providers and the currently running pipeline.

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
                context['errorMessage'] = _(unicode(msg))
                break

    return context


def _external_auth_intercept(request, mode):
    """Allow external auth to intercept a login/registration request.

    Arguments:
        request (Request): The original request.
        mode (str): Either "login" or "register"

    Returns:
        Response or None

    """
    if mode == "login":
        return external_auth_login(request)
    elif mode == "register":
        return external_auth_register(request)
