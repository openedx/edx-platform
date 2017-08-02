""" Views for a student's account information. """

import json
import logging
import urlparse
from datetime import datetime

import pytz
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import resolve, reverse
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django_countries import countries

import third_party_auth
from commerce.models import CommerceConfiguration
from edxmako.shortcuts import render_to_response, render_to_string
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.djangoapps.external_auth.login_and_register import login as external_auth_login
from openedx.core.djangoapps.external_auth.login_and_register import register as external_auth_register
from openedx.core.djangoapps.lang_pref.api import all_languages, released_languages
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.theming.helpers import is_request_in_themed_site
from openedx.core.djangoapps.user_api.accounts.api import request_password_change
from openedx.core.djangoapps.user_api.errors import UserNotFound
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.time_zone_utils import TIME_ZONE_CHOICES
from openedx.features.enterprise_support.api import enterprise_customer_for_request
from student.helpers import destroy_oauth_tokens, get_next_url_for_login_page
from student.models import UserProfile
from student.views import register_user as old_register_view
from student.views import signin_user as old_login_view
from third_party_auth import pipeline
from third_party_auth.decorators import xframe_allow_whitelisted
from util.bad_request_rate_limiter import BadRequestRateLimiter
from util.date_utils import strftime_localized

AUDIT_LOG = logging.getLogger("audit")
log = logging.getLogger(__name__)
User = get_user_model()  # pylint:disable=invalid-name


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
    if request.user.is_authenticated():
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
                    return redirect(
                        pipeline.get_login_url(provider_id, pipeline.AUTH_ENTRY_LOGIN, redirect_url=redirect_to)
                    )
                third_party_auth_hint = provider_id
                initial_mode = "hinted_login"
        except (KeyError, ValueError, IndexError):
            pass

    # If this is a themed site, revert to the old login/registration pages.
    # We need to do this for now to support existing themes.
    # Themed sites can use the new logistration page by setting
    # 'ENABLE_COMBINED_LOGIN_REGISTRATION' in their
    # configuration settings.
    if is_request_in_themed_site() and not configuration_helpers.get_value('ENABLE_COMBINED_LOGIN_REGISTRATION', False):
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

            # Include form descriptions retrieved from the user API.
            # We could have the JS client make these requests directly,
            # but we include them in the initial page load to avoid
            # the additional round-trip to the server.
            'login_form_desc': json.loads(form_descriptions['login']),
            'registration_form_desc': json.loads(form_descriptions['registration']),
            'password_reset_form_desc': json.loads(form_descriptions['password_reset']),
            'account_creation_allowed': configuration_helpers.get_value(
                'ALLOW_PUBLIC_ACCOUNT_CREATION', settings.FEATURES.get('ALLOW_PUBLIC_ACCOUNT_CREATION', True))
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

    context = update_context_for_enterprise(request, context)

    response = render_to_response('student_account/login_and_register.html', context)

    # Remove enterprise cookie so that subsequent requests show default login page.
    response.delete_cookie(
        configuration_helpers.get_value("ENTERPRISE_CUSTOMER_COOKIE_NAME", settings.ENTERPRISE_CUSTOMER_COOKIE_NAME),
        domain=configuration_helpers.get_value("BASE_COOKIE_DOMAIN", settings.BASE_COOKIE_DOMAIN),
    )

    return response


@require_http_methods(['POST'])
def password_change_request_handler(request):
    """Handle password change requests originating from the account page.

    Uses the Account API to email the user a link to the password reset page.

    Note:
        The next step in the password reset process (confirmation) is currently handled
        by student.views.password_reset_confirm_wrapper, a custom wrapper around Django's
        password reset confirmation view.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the email was sent successfully
        HttpResponse: 400 if there is no 'email' POST parameter
        HttpResponse: 403 if the client has been rate limited
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        POST /account/password

    """

    limiter = BadRequestRateLimiter()
    if limiter.is_rate_limit_exceeded(request):
        AUDIT_LOG.warning("Password reset rate limit exceeded")
        return HttpResponseForbidden()

    user = request.user
    # Prefer logged-in user's email
    email = user.email if user.is_authenticated() else request.POST.get('email')

    if email:
        try:
            request_password_change(email, request.get_host(), request.is_secure())
            user = user if user.is_authenticated() else User.objects.get(email=email)
            destroy_oauth_tokens(user)
        except UserNotFound:
            AUDIT_LOG.info("Invalid password reset attempt")
            # Increment the rate limit counter
            limiter.tick_bad_request_counter(request)

        return HttpResponse(status=200)
    else:
        return HttpResponseBadRequest(_("No email address provided."))


def update_context_for_enterprise(request, context):
    """
    Take the processed context produced by the view, determine if it's relevant
    to a particular Enterprise Customer, and update it to include that customer's
    enterprise metadata.
    """

    context = context.copy()

    sidebar_context = enterprise_sidebar_context(request)

    if sidebar_context:
        context['data']['registration_form_desc']['fields'] = enterprise_fields_only(
            context['data']['registration_form_desc']
        )
        context.update(sidebar_context)
        context['enable_enterprise_sidebar'] = True
        context['data']['hide_auth_warnings'] = True
    else:
        context['enable_enterprise_sidebar'] = False

    return context


def enterprise_fields_only(fields):
    """
    Take the received field definition, and exclude those fields that we don't want
    to require if the user is going to be a member of an Enterprise Customer.
    """
    enterprise_exclusions = configuration_helpers.get_value(
        'ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS',
        settings.ENTERPRISE_EXCLUDED_REGISTRATION_FIELDS
    )
    return [field for field in fields['fields'] if field['name'] not in enterprise_exclusions]


def enterprise_sidebar_context(request):
    """
    Given the current request, render the HTML of a sidebar for the current
    logistration view that depicts Enterprise-related information.
    """
    enterprise_customer = enterprise_customer_for_request(request)

    if not enterprise_customer:
        return {}

    platform_name = configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)

    if enterprise_customer.branding_configuration.logo:
        enterprise_logo_url = enterprise_customer.branding_configuration.logo.url
    else:
        enterprise_logo_url = ''

    if getattr(enterprise_customer.branding_configuration, 'welcome_message', None):
        branded_welcome_template = enterprise_customer.branding_configuration.welcome_message
    else:
        branded_welcome_template = configuration_helpers.get_value(
            'ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE',
            settings.ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE
        )

    branded_welcome_string = branded_welcome_template.format(
        start_bold=u'<b>',
        end_bold=u'</b>',
        enterprise_name=enterprise_customer.name,
        platform_name=platform_name
    )

    platform_welcome_template = configuration_helpers.get_value(
        'ENTERPRISE_PLATFORM_WELCOME_TEMPLATE',
        settings.ENTERPRISE_PLATFORM_WELCOME_TEMPLATE
    )
    platform_welcome_string = platform_welcome_template.format(platform_name=platform_name)

    context = {
        'enterprise_name': enterprise_customer.name,
        'enterprise_logo_url': enterprise_logo_url,
        'enterprise_branded_welcome_string': branded_welcome_string,
        'platform_welcome_string': platform_welcome_string,
    }

    return context


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
    }

    if third_party_auth.is_enabled():
        enterprise_customer = enterprise_customer_for_request(request)
        if not enterprise_customer:
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

            if current_provider is not None:
                context["currentProvider"] = current_provider.name
                context["finishAuthUrl"] = pipeline.get_complete_url(current_provider.backend_name)

                if current_provider.skip_registration_form:
                    # For enterprise (and later for everyone), we need to get explicit consent to the
                    # Terms of service instead of auto submitting the registration form outright.
                    if not enterprise_customer:
                        # As a reliable way of "skipping" the registration form, we just submit it automatically
                        context["autoSubmitRegForm"] = True
                    else:
                        context["autoRegisterWelcomeMessage"] = (
                            'Thank you for joining {}. '
                            'Just a couple steps before you start learning!'
                        ).format(
                            configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
                        )
                        context["registerFormSubmitButtonText"] = _("Continue")

        # Check for any error messages we may want to display:
        for msg in messages.get_messages(request):
            if msg.extra_tags.split()[0] == "social-auth":
                # msg may or may not be translated. Try translating [again] in case we are able to:
                context['errorMessage'] = _(unicode(msg))  # pylint: disable=translation-of-non-string
                break

    return context


def _get_form_descriptions(request):
    """Retrieve form descriptions from the user API.

    Arguments:
        request (HttpRequest): The original request, used to retrieve session info.

    Returns:
        dict: Keys are 'login', 'registration', and 'password_reset';
            values are the JSON-serialized form descriptions.

    """
    return {
        'login': _local_server_get('/user_api/v1/account/login_session/', request.session),
        'registration': _local_server_get('/user_api/v1/account/registration/', request.session),
        'password_reset': _local_server_get('/user_api/v1/account/password_reset/', request.session)
    }


def _local_server_get(url, session):
    """Simulate a server-server GET request for an in-process API.

    Arguments:
        url (str): The URL of the request (excluding the protocol and domain)
        session (SessionStore): The session of the original request,
            used to get past the CSRF checks.

    Returns:
        str: The content of the response

    """
    # Since the user API is currently run in-process,
    # we simulate the server-server API call by constructing
    # our own request object.  We don't need to include much
    # information in the request except for the session
    # (to get past through CSRF validation)
    request = HttpRequest()
    request.method = "GET"
    request.session = session

    # Call the Django view function, simulating
    # the server-server API call
    view, args, kwargs = resolve(url)
    response = view(request, *args, **kwargs)

    # Return the content of the response
    return response.content


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


def get_user_orders(user):
    """Given a user, get the detail of all the orders from the Ecommerce service.

    Args:
        user (User): The user to authenticate as when requesting ecommerce.

    Returns:
        list of dict, representing orders returned by the Ecommerce service.
    """
    no_data = []
    user_orders = []
    commerce_configuration = CommerceConfiguration.current()
    user_query = {'username': user.username}

    use_cache = commerce_configuration.is_cache_enabled
    cache_key = commerce_configuration.CACHE_KEY + '.' + str(user.id) if use_cache else None
    api = ecommerce_api_client(user)
    commerce_user_orders = get_edx_api_data(
        commerce_configuration, 'orders', api=api, querystring=user_query, cache_key=cache_key
    )

    for order in commerce_user_orders:
        if order['status'].lower() == 'complete':
            date_placed = datetime.strptime(order['date_placed'], "%Y-%m-%dT%H:%M:%SZ")
            order_data = {
                'number': order['number'],
                'price': order['total_excl_tax'],
                'order_date': strftime_localized(date_placed, 'SHORT_DATE'),
                'receipt_url': EcommerceService().get_receipt_page_url(order['number']),
                'lines': order['lines'],
            }
            user_orders.append(order_data)

    return user_orders


@login_required
@require_http_methods(['GET'])
def account_settings(request):
    """Render the current user's account settings page.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        GET /account/settings

    """
    return render_to_response('student_account/account_settings.html', account_settings_context(request))


@login_required
@require_http_methods(['GET'])
def finish_auth(request):  # pylint: disable=unused-argument
    """ Following logistration (1st or 3rd party), handle any special query string params.

    See FinishAuthView.js for details on the query string params.

    e.g. auto-enroll the user in a course, set email opt-in preference.

    This view just displays a "Please wait" message while AJAX calls are made to enroll the
    user in the course etc. This view is only used if a parameter like "course_id" is present
    during login/registration/third_party_auth. Otherwise, there is no need for it.

    Ideally this view will finish and redirect to the next step before the user even sees it.

    Args:
        request (HttpRequest)

    Returns:
        HttpResponse: 200 if the page was sent successfully
        HttpResponse: 302 if not logged in (redirect to login page)
        HttpResponse: 405 if using an unsupported HTTP method

    Example usage:

        GET /account/finish_auth/?course_id=course-v1:blah&enrollment_action=enroll

    """
    return render_to_response('student_account/finish_auth.html', {
        'disable_courseware_js': True,
        'disable_footer': True,
    })


def account_settings_context(request):
    """ Context for the account settings page.

    Args:
        request: The request object.

    Returns:
        dict

    """
    user = request.user

    year_of_birth_options = [(unicode(year), unicode(year)) for year in UserProfile.VALID_YEARS]
    try:
        user_orders = get_user_orders(user)
    except:  # pylint: disable=bare-except
        log.exception('Error fetching order history from Otto.')
        # Return empty order list as account settings page expect a list and
        # it will be broken if exception raised
        user_orders = []

    context = {
        'auth': {},
        'duplicate_provider': None,
        'nav_hidden': True,
        'fields': {
            'country': {
                'options': list(countries),
            }, 'gender': {
                'options': [(choice[0], _(choice[1])) for choice in UserProfile.GENDER_CHOICES],  # pylint: disable=translation-of-non-string
            }, 'language': {
                'options': released_languages(),
            }, 'level_of_education': {
                'options': [(choice[0], _(choice[1])) for choice in UserProfile.LEVEL_OF_EDUCATION_CHOICES],  # pylint: disable=translation-of-non-string
            }, 'password': {
                'url': reverse('password_reset'),
            }, 'year_of_birth': {
                'options': year_of_birth_options,
            }, 'preferred_language': {
                'options': all_languages(),
            }, 'time_zone': {
                'options': TIME_ZONE_CHOICES,
            }
        },
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'password_reset_support_link': configuration_helpers.get_value(
            'PASSWORD_RESET_SUPPORT_LINK', settings.PASSWORD_RESET_SUPPORT_LINK
        ) or settings.SUPPORT_SITE_LINK,
        'user_accounts_api_url': reverse("accounts_api", kwargs={'username': user.username}),
        'user_preferences_api_url': reverse('preferences_api', kwargs={'username': user.username}),
        'disable_courseware_js': True,
        'show_program_listing': ProgramsApiConfig.is_enabled(),
        'order_history': user_orders
    }

    if third_party_auth.is_enabled():
        # If the account on the third party provider is already connected with another edX account,
        # we display a message to the user.
        context['duplicate_provider'] = pipeline.get_duplicate_provider(messages.get_messages(request))

        auth_states = pipeline.get_provider_user_states(user)

        context['auth']['providers'] = [{
            'id': state.provider.provider_id,
            'name': state.provider.name,  # The name of the provider e.g. Facebook
            'connected': state.has_account,  # Whether the user's edX account is connected with the provider.
            # If the user is not connected, they should be directed to this page to authenticate
            # with the particular provider, as long as the provider supports initiating a login.
            'connect_url': pipeline.get_login_url(
                state.provider.provider_id,
                pipeline.AUTH_ENTRY_ACCOUNT_SETTINGS,
                # The url the user should be directed to after the auth process has completed.
                redirect_url=reverse('account_settings'),
            ),
            'accepts_logins': state.provider.accepts_logins,
            # If the user is connected, sending a POST request to this url removes the connection
            # information for this provider from their edX account.
            'disconnect_url': pipeline.get_disconnect_url(state.provider.provider_id, state.association_id),
            # We only want to include providers if they are either currently available to be logged
            # in with, or if the user is already authenticated with them.
        } for state in auth_states if state.provider.display_for_login or state.has_account]

    return context
