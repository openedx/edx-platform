from __future__ import unicode_literals

import hashlib

import six
from django.conf import settings
from django.utils.translation import ugettext as _
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


def update_third_party_auth_context_for_enterprise(context, enterprise_customer=None):
    """
    Return updated context of third party auth with modified for enterprise.

    Arguments:
        context (dict): Context for third party auth providers and auth pipeline.
        enterprise_customer (dict): data for enterprise customer

    Returns:
         context (dict): Updated context of third party auth with modified
         `errorMessage`.
    """
    if enterprise_customer and context['errorMessage']:
        context['errorMessage'] = Text(_(
            u'We are sorry, you are not authorized to access {platform_name} via this channel. '
            u'Please contact your {enterprise} administrator in order to access {platform_name} '
            u'or contact {edx_support_link}.{line_break}'
            u'{line_break}'
            u'Error Details:{line_break}{error_message}')
        ).format(
            platform_name=configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
            enterprise=enterprise_customer['name'],
            error_message=context['errorMessage'],
            edx_support_link=HTML(
                '<a href="{edx_support_url}">{support_url_name}</a>'
            ).format(
                edx_support_url=configuration_helpers.get_value(
                    'SUPPORT_SITE_LINK', settings.SUPPORT_SITE_LINK
                ),
                support_url_name=_('edX Support'),
            ),
            line_break=HTML('<br/>')
        )

    return context
