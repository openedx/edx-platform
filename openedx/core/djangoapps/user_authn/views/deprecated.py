""" User Authn code for deprecated views. """
import warnings

from django.conf import settings
from django.contrib import messages
from django.core.validators import ValidationError
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from six import text_type, iteritems

from edxmako.shortcuts import render_to_response

from openedx.core.djangoapps.user_authn.views.register import create_account_with_params
from openedx.core.djangoapps.user_authn.cookies import set_logged_in_cookies
from openedx.core.djangoapps.external_auth.login_and_register import login as external_auth_login
from openedx.core.djangoapps.external_auth.login_and_register import register as external_auth_register
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.config.waffle import PREVENT_AUTH_USER_WRITES, SYSTEM_MAINTENANCE_MSG, waffle
from student.helpers import (
    auth_pipeline_urls,
    get_next_url_for_login_page
)
from student.helpers import AccountValidationError
import third_party_auth
from third_party_auth import pipeline, provider
from util.json_request import JsonResponse


@ensure_csrf_cookie
def signin_user(request):
    """Deprecated. To be replaced by :class:`user_authn.views.login_form.login_and_registration_form`."""
    external_auth_response = external_auth_login(request)
    if external_auth_response is not None:
        return external_auth_response
    # Determine the URL to redirect to following login:
    redirect_to = get_next_url_for_login_page(request)
    if request.user.is_authenticated:
        return redirect(redirect_to)

    third_party_auth_error = None
    for msg in messages.get_messages(request):
        if msg.extra_tags.split()[0] == "social-auth":
            # msg may or may not be translated. Try translating [again] in case we are able to:
            third_party_auth_error = _(text_type(msg))
            break

    context = {
        'login_redirect_url': redirect_to,  # This gets added to the query string of the "Sign In" button in the header
        # Bool injected into JS to submit form if we're inside a running third-
        # party auth pipeline; distinct from the actual instance of the running
        # pipeline, if any.
        'pipeline_running': 'true' if pipeline.running(request) else 'false',
        'pipeline_url': auth_pipeline_urls(pipeline.AUTH_ENTRY_LOGIN, redirect_url=redirect_to),
        'platform_name': configuration_helpers.get_value(
            'platform_name',
            settings.PLATFORM_NAME
        ),
        'third_party_auth_error': third_party_auth_error
    }

    return render_to_response('login.html', context)


@ensure_csrf_cookie
def register_user(request, extra_context=None):
    """
    Deprecated. To be replaced by :class:`user_authn.views.login_form.login_and_registration_form`.
    """
    # Determine the URL to redirect to following login:
    redirect_to = get_next_url_for_login_page(request)
    if request.user.is_authenticated:
        return redirect(redirect_to)

    external_auth_response = external_auth_register(request)
    if external_auth_response is not None:
        return external_auth_response

    context = {
        'login_redirect_url': redirect_to,  # This gets added to the query string of the "Sign In" button in the header
        'email': '',
        'name': '',
        'running_pipeline': None,
        'pipeline_urls': auth_pipeline_urls(pipeline.AUTH_ENTRY_REGISTER, redirect_url=redirect_to),
        'platform_name': configuration_helpers.get_value(
            'platform_name',
            settings.PLATFORM_NAME
        ),
        'selected_provider': '',
        'username': '',
    }

    if extra_context is not None:
        context.update(extra_context)

    if context.get("extauth_domain", '').startswith(settings.SHIBBOLETH_DOMAIN_PREFIX):
        return render_to_response('register-shib.html', context)

    # If third-party auth is enabled, prepopulate the form with data from the
    # selected provider.
    if third_party_auth.is_enabled() and pipeline.running(request):
        running_pipeline = pipeline.get(request)
        current_provider = provider.Registry.get_from_pipeline(running_pipeline)
        if current_provider is not None:
            overrides = current_provider.get_register_form_data(running_pipeline.get('kwargs'))
            overrides['running_pipeline'] = running_pipeline
            overrides['selected_provider'] = current_provider.name
            context.update(overrides)

    return render_to_response('register.html', context)


@csrf_exempt
@transaction.non_atomic_requests
def create_account(request, post_override=None):
    """
    Deprecated. Use RegistrationView instead.
    JSON call to create new edX account.
    Used by form in signup_modal.html, which is included into header.html
    """
    # Check if ALLOW_PUBLIC_ACCOUNT_CREATION flag turned off to restrict user account creation
    if not configuration_helpers.get_value(
            'ALLOW_PUBLIC_ACCOUNT_CREATION',
            settings.FEATURES.get('ALLOW_PUBLIC_ACCOUNT_CREATION', True)
    ):
        return HttpResponseForbidden(_("Account creation not allowed."))

    if waffle().is_enabled(PREVENT_AUTH_USER_WRITES):
        return HttpResponseForbidden(SYSTEM_MAINTENANCE_MSG)

    warnings.warn("Please use RegistrationView instead.", DeprecationWarning)

    try:
        user = create_account_with_params(request, post_override or request.POST)
    except AccountValidationError as exc:
        return JsonResponse({'success': False, 'value': text_type(exc), 'field': exc.field}, status=400)
    except ValidationError as exc:
        field, error_list = next(iteritems(exc.message_dict))
        return JsonResponse(
            {
                "success": False,
                "field": field,
                "value": ' '.join(error_list),
            },
            status=400
        )

    redirect_url = None  # The AJAX method calling should know the default destination upon success

    # Resume the third-party-auth pipeline if necessary.
    if third_party_auth.is_enabled() and pipeline.running(request):
        running_pipeline = pipeline.get(request)
        redirect_url = pipeline.get_complete_url(running_pipeline['backend'])

    response = JsonResponse({
        'success': True,
        'redirect_url': redirect_url,
    })
    set_logged_in_cookies(request, response, user)
    return response
