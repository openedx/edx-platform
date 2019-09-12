from __future__ import unicode_literals

import hashlib
import json

import six
from django.conf import settings
from django.utils.translation import ugettext as _

import third_party_auth
from third_party_auth import pipeline
from enterprise.models import EnterpriseCustomerUser

from openedx.core.djangoapps.user_authn.cookies import standard_cookie_settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.markup import HTML, Text


def get_cache_key(**kwargs):
    """
    Get MD5 encoded cache key for given arguments.

    Here is the format of key before MD5 encryption.
        key1:value1__key2:value2 ...

    Example:
        >>> get_cache_key(site_domain="example.com", resource="enterprise-learner")
        # Here is key format for above call
        # "site_domain:example.com__resource:enterprise-learner"
        a54349175618ff1659dee0978e3149ca

    Arguments:
        **kwargs: Key word arguments that need to be present in cache key.

    Returns:
         An MD5 encoded key uniquely identified by the key word arguments.
    """
    key = '__'.join(['{}:{}'.format(item, value) for item, value in six.iteritems(kwargs)])

    return hashlib.md5(key).hexdigest()


def update_logistration_context_for_enterprise(request, context, enterprise_customer):
    """
    Take the processed context produced by the view, determine if it's relevant
    to a particular Enterprise Customer, and update it to include that customer's
    enterprise metadata.

     Arguments:
         request (HttpRequest): The request for the logistration page.
         context (dict): Context for logistration page.
         enterprise_customer (dict): data for enterprise customer

    """
    sidebar_context = {}
    if enterprise_customer:
        sidebar_context = get_enterprise_sidebar_context(enterprise_customer)

    if sidebar_context:
        context['data']['registration_form_desc']['fields'] = enterprise_fields_only(
            context['data']['registration_form_desc']
        )
        context.update(sidebar_context)
        context['enable_enterprise_sidebar'] = True
        context['data']['hide_auth_warnings'] = True
        context['data']['enterprise_name'] = enterprise_customer['name']
    else:
        context['enable_enterprise_sidebar'] = False

    update_third_party_auth_context_for_enterprise(request, context, enterprise_customer)


def get_enterprise_sidebar_context(enterprise_customer):
    """
    Get context information for enterprise sidebar for the given enterprise customer.

    Enterprise Sidebar Context has the following key-value pairs.
    {
        'enterprise_name': 'Enterprise Name',
        'enterprise_logo_url': 'URL of the enterprise logo image',
        'enterprise_branded_welcome_string': 'Human readable welcome message customized for the enterprise',
        'platform_welcome_string': 'Human readable welcome message for an enterprise learner',
    }
    """
    platform_name = configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)

    branding_configuration = enterprise_customer.get('branding_configuration', {})
    logo_url = branding_configuration.get('logo', '') if isinstance(branding_configuration, dict) else ''

    branded_welcome_template = configuration_helpers.get_value(
        'ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE',
        settings.ENTERPRISE_SPECIFIC_BRANDED_WELCOME_TEMPLATE
    )

    branded_welcome_string = Text(branded_welcome_template).format(
        start_bold=HTML('<b>'),
        end_bold=HTML('</b>'),
        line_break=HTML('<br/>'),
        enterprise_name=enterprise_customer['name'],
        platform_name=platform_name,
        privacy_policy_link_start=HTML("<a href='{pp_url}' rel='noopener' target='_blank'>").format(
            pp_url=settings.MKTG_URLS.get('PRIVACY', 'https://www.edx.org/edx-privacy-policy')
        ),
        privacy_policy_link_end=HTML("</a>"),
    )

    platform_welcome_template = configuration_helpers.get_value(
        'ENTERPRISE_PLATFORM_WELCOME_TEMPLATE',
        settings.ENTERPRISE_PLATFORM_WELCOME_TEMPLATE
    )
    platform_welcome_string = platform_welcome_template.format(platform_name=platform_name)

    return {
        'enterprise_name': enterprise_customer['name'],
        'enterprise_logo_url': logo_url,
        'enterprise_branded_welcome_string': branded_welcome_string,
        'platform_welcome_string': platform_welcome_string,
    }


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


def update_third_party_auth_context_for_enterprise(request, context, enterprise_customer=None):
    """
    Return updated context of third party auth with modified for enterprise.

    Arguments:
        request (HttpRequest): The request for the logistration page.
        context (dict): Context for third party auth providers and auth pipeline.
        enterprise_customer (dict): data for enterprise customer

    Returns:
         context (dict): Updated context of third party auth with modified
         `errorMessage`.
    """
    if context['data']['third_party_auth']['errorMessage']:
        context['data']['third_party_auth']['errorMessage'] = Text(_(
            u'We are sorry, you are not authorized to access {platform_name} via this channel. '
            u'Please contact your learning administrator or manager in order to access {platform_name}.'
            u'{line_break}{line_break}'
            u'Error Details:{line_break}{error_message}')
        ).format(
            platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            error_message=context['data']['third_party_auth']['errorMessage'],
            line_break=HTML('<br/>')
        )

    if enterprise_customer:
        context['data']['third_party_auth']['providers'] = []
        context['data']['third_party_auth']['secondaryProviders'] = []

    running_pipeline = pipeline.get(request)
    if running_pipeline is not None:
        current_provider = third_party_auth.provider.Registry.get_from_pipeline(running_pipeline)
        if current_provider is not None and current_provider.skip_registration_form and enterprise_customer:
            # For enterprise (and later for everyone), we need to get explicit consent to the
            # Terms of service instead of auto submitting the registration form outright.
            context['data']['third_party_auth']['autoSubmitRegForm'] = False
            context['data']['third_party_auth']['autoRegisterWelcomeMessage'] = Text(_(
                'Thank you for joining {platform_name}. '
                'Just a couple steps before you start learning!')
            ).format(
                platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME)
            )
            context['data']['third_party_auth']['registerFormSubmitButtonText'] = _('Continue')

    return context


def handle_enterprise_cookies_for_logistration(request, response, context):
    """
    Helper method for setting or deleting enterprise cookies on logistration response.

    Arguments:
        request (HttpRequest): The request for the logistration page.
        response (HttpResponse): The response for the logistration page.
        context (dict): Context for logistration page.

    """
    # This cookie can be used for tests or minor features,
    # but should not be used for payment related or other critical work
    # since users can edit their cookies
    _set_experiments_is_enterprise_cookie(request, response, context['enable_enterprise_sidebar'])

    # Remove enterprise cookie so that subsequent requests show default login page.
    response.delete_cookie(
        configuration_helpers.get_value('ENTERPRISE_CUSTOMER_COOKIE_NAME', settings.ENTERPRISE_CUSTOMER_COOKIE_NAME),
        domain=configuration_helpers.get_value('BASE_COOKIE_DOMAIN', settings.BASE_COOKIE_DOMAIN),
    )


def _set_experiments_is_enterprise_cookie(request, response, experiments_is_enterprise):
    """ Sets the experiments_is_enterprise cookie on the response.
    This cookie can be used for tests or minor features,
    but should not be used for payment related or other critical work
    since users can edit their cookies
    """
    cookie_settings = standard_cookie_settings(request)

    response.set_cookie(
        'experiments_is_enterprise',
        json.dumps(experiments_is_enterprise),
        **cookie_settings
    )


def update_account_settings_context_for_enterprise(context, enterprise_customer):
    """
    Take processed context for account settings page and update it taking enterprise customer into account.

     Arguments:
         context (dict): Context for account settings page.
         enterprise_customer (dict): data for enterprise customer

    """
    enterprise_context = {
        'enterprise_name': None,
        'sync_learner_profile_data': False,
        'edx_support_url': configuration_helpers.get_value('SUPPORT_SITE_LINK', settings.SUPPORT_SITE_LINK),
        'enterprise_readonly_account_fields': {
            'fields': settings.ENTERPRISE_READONLY_ACCOUNT_FIELDS
        }
    }

    if enterprise_customer:
        enterprise_context['enterprise_name'] = enterprise_customer['name']
        identity_provider = third_party_auth.provider.Registry.get(
            provider_id=enterprise_customer['identity_provider'],
        )
        if identity_provider:
            enterprise_context['sync_learner_profile_data'] = identity_provider.sync_learner_profile_data

    context.update(enterprise_context)


def get_enterprise_learner_generic_name(request):
    """
    Get a generic name concatenating the Enterprise Customer name and 'Learner'.

    ENT-924: Temporary solution for hiding potentially sensitive SSO names.
    When a more complete solution is put in place, delete this function and all of its uses.
    """
    # Prevent a circular import. This function makes sense to be in this module though. And see function description.
    from openedx.features.enterprise_support.api import enterprise_customer_for_request
    enterprise_customer = enterprise_customer_for_request(request)
    return (
        enterprise_customer['name'] + 'Learner'
        if enterprise_customer and enterprise_customer['replace_sensitive_sso_username']
        else ''
    )


def is_enterprise_learner(user):
    """
    Check if the given user belongs to an enterprise.

    Arguments:
        user (User): Django User object.

    Returns:
        (bool): True if given user is an enterprise learner.
    """
    return EnterpriseCustomerUser.objects.filter(user_id=user.id).exists()
