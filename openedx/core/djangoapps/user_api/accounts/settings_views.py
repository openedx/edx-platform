""" Views related to Account Settings. """


import logging
from datetime import datetime

import six
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods
from django_countries import countries

from common.djangoapps import third_party_auth
from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.commerce.models import CommerceConfiguration
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref.api import all_languages, released_languages
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.accounts.toggles import (
    should_redirect_to_account_microfrontend,
    should_redirect_to_order_history_microfrontend
)
from openedx.core.djangoapps.user_api.preferences.api import get_user_preferences
from openedx.core.lib.edx_api_utils import get_edx_api_data
from openedx.core.lib.time_zone_utils import TIME_ZONE_CHOICES
from openedx.features.enterprise_support.api import enterprise_customer_for_request
from openedx.features.enterprise_support.utils import update_account_settings_context_for_enterprise
from common.djangoapps.student.models import UserProfile
from common.djangoapps.third_party_auth import pipeline
from common.djangoapps.util.date_utils import strftime_localized

log = logging.getLogger(__name__)


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
    if should_redirect_to_account_microfrontend():
        url = settings.ACCOUNT_MICROFRONTEND_URL

        duplicate_provider = pipeline.get_duplicate_provider(messages.get_messages(request))
        if duplicate_provider:
            url = '{url}?{params}'.format(
                url=url,
                params=six.moves.urllib.parse.urlencode({
                    'duplicate_provider': duplicate_provider,
                }),
            )

        return redirect(url)

    context = account_settings_context(request)
    return render_to_response('student_account/account_settings.html', context)


def account_settings_context(request):
    """ Context for the account settings page.

    Args:
        request: The request object.

    Returns:
        dict

    """
    user = request.user

    year_of_birth_options = [(six.text_type(year), six.text_type(year)) for year in UserProfile.VALID_YEARS]
    try:
        user_orders = get_user_orders(user)
    except:  # pylint: disable=bare-except
        log.exception('Error fetching order history from Otto.')
        # Return empty order list as account settings page expect a list and
        # it will be broken if exception raised
        user_orders = []

    beta_language = {}
    dark_lang_config = DarkLangConfig.current()
    if dark_lang_config.enable_beta_languages:
        user_preferences = get_user_preferences(user)
        pref_language = user_preferences.get('pref-lang')
        if pref_language in dark_lang_config.beta_languages_list:
            beta_language['code'] = pref_language
            beta_language['name'] = settings.LANGUAGE_DICT.get(pref_language)

    context = {
        'auth': {},
        'duplicate_provider': None,
        'nav_hidden': True,
        'fields': {
            'country': {
                'options': list(countries),
            }, 'gender': {
                'options': [(choice[0], _(choice[1])) for choice in UserProfile.GENDER_CHOICES],
            }, 'language': {
                'options': released_languages(),
            }, 'level_of_education': {
                'options': [(choice[0], _(choice[1])) for choice in UserProfile.LEVEL_OF_EDUCATION_CHOICES],
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
        'show_dashboard_tabs': True,
        'order_history': user_orders,
        'disable_order_history_tab': should_redirect_to_order_history_microfrontend(),
        'enable_account_deletion': configuration_helpers.get_value(
            'ENABLE_ACCOUNT_DELETION', settings.FEATURES.get('ENABLE_ACCOUNT_DELETION', False)
        ),
        'extended_profile_fields': _get_extended_profile_fields(),
        'beta_language': beta_language,
    }

    enterprise_customer = enterprise_customer_for_request(request)
    update_account_settings_context_for_enterprise(context, enterprise_customer, user)

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


def get_user_orders(user):
    """Given a user, get the detail of all the orders from the Ecommerce service.

    Args:
        user (User): The user to authenticate as when requesting ecommerce.

    Returns:
        list of dict, representing orders returned by the Ecommerce service.
    """
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


def _get_extended_profile_fields():
    """Retrieve the extended profile fields from site configuration to be shown on the
       Account Settings page

    Returns:
        A list of dicts. Each dict corresponds to a single field. The keys per field are:
            "field_name"  : name of the field stored in user_profile.meta
            "field_label" : The label of the field.
            "field_type"  : TextField or ListField
            "field_options": a list of tuples for options in the dropdown in case of ListField
    """

    extended_profile_fields = []
    fields_already_showing = ['username', 'name', 'email', 'pref-lang', 'country', 'time_zone', 'level_of_education',
                              'gender', 'year_of_birth', 'language_proficiencies', 'social_links']

    field_labels_map = {
        "first_name": _(u"First Name"),
        "last_name": _(u"Last Name"),
        "city": _(u"City"),
        "state": _(u"State/Province/Region"),
        "company": _(u"Company"),
        "title": _(u"Title"),
        "job_title": _(u"Job Title"),
        "mailing_address": _(u"Mailing address"),
        "goals": _(u"Tell us why you're interested in {platform_name}").format(
            platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME)
        ),
        "profession": _(u"Profession"),
        "specialty": _(u"Specialty")
    }

    extended_profile_field_names = configuration_helpers.get_value('extended_profile_fields', [])
    for field_to_exclude in fields_already_showing:
        if field_to_exclude in extended_profile_field_names:
            extended_profile_field_names.remove(field_to_exclude)

    extended_profile_field_options = configuration_helpers.get_value('EXTRA_FIELD_OPTIONS', [])
    extended_profile_field_option_tuples = {}
    for field in extended_profile_field_options.keys():
        field_options = extended_profile_field_options[field]
        extended_profile_field_option_tuples[field] = [(option.lower(), option) for option in field_options]

    for field in extended_profile_field_names:
        field_dict = {
            "field_name": field,
            "field_label": field_labels_map.get(field, field),
        }

        field_options = extended_profile_field_option_tuples.get(field)
        if field_options:
            field_dict["field_type"] = "ListField"
            field_dict["field_options"] = field_options
        else:
            field_dict["field_type"] = "TextField"
        extended_profile_fields.append(field_dict)

    return extended_profile_fields
