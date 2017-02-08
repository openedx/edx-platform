"""
Helpers to access the enterprise app
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
import logging

from django.utils.http import urlencode

try:
    from enterprise.models import EnterpriseCustomer
    from enterprise import utils as enterprise_utils
    from enterprise.tpa_pipeline import (
        active_provider_requests_data_sharing,
        active_provider_enforces_data_sharing,
        get_enterprise_customer_for_request,
    )
    from enterprise.utils import consent_necessary_for_course

except ImportError:
    pass

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS = 'enterprise_customer_branding_override_details'
LOGGER = logging.getLogger("edx.enterprise_helpers")


def enterprise_enabled():
    """
    Determines whether the Enterprise app is installed
    """
    return 'enterprise' in settings.INSTALLED_APPS and getattr(settings, 'ENABLE_ENTERPRISE_INTEGRATION', True)


def consent_needed_for_course(user, course_id):
    """
    Wrap the enterprise app check to determine if the user needs to grant
    data sharing permissions before accessing a course.
    """
    if not enterprise_enabled():
        return False
    return consent_necessary_for_course(user, course_id)


def get_course_specific_consent_url(request, course_id, return_to):
    """
    Build a URL to redirect the user to the Enterprise app to provide data sharing
    consent for a specific course ID.
    """
    url_params = {
        'course_id': course_id,
        'next': request.build_absolute_uri(reverse(return_to, args=(course_id,)))
    }
    querystring = urlencode(url_params)
    full_url = reverse('grant_data_sharing_permissions') + '?' + querystring
    LOGGER.info('Redirecting to %s to complete data sharing consent', full_url)
    return full_url


def insert_enterprise_pipeline_elements(pipeline):
    """
    If the enterprise app is enabled, insert additional elements into the
    pipeline so that data sharing consent views are used.
    """
    if not enterprise_enabled():
        return

    additional_elements = (
        'enterprise.tpa_pipeline.set_data_sharing_consent_record',
        'enterprise.tpa_pipeline.verify_data_sharing_consent',
    )
    # Find the item we need to insert the data sharing consent elements before
    insert_point = pipeline.index('social.pipeline.social_auth.load_extra_data')

    for index, element in enumerate(additional_elements):
        pipeline.insert(insert_point + index, element)


def get_enterprise_customer_logo_url(request):
    """
    Client API operation adapter/wrapper.
    """

    if not enterprise_enabled():
        return None

    parameter = get_enterprise_branding_filter_param(request)
    if not parameter:
        return None

    provider_id = parameter.get('provider_id', None)
    ec_uuid = parameter.get('ec_uuid', None)

    if provider_id:
        branding_info = enterprise_utils.get_enterprise_branding_info_by_provider_id(identity_provider_id=provider_id)
    elif ec_uuid:
        branding_info = enterprise_utils.get_enterprise_branding_info_by_ec_uuid(ec_uuid=ec_uuid)

    logo_url = None
    if branding_info and branding_info.logo:
        logo_url = branding_info.logo.url

    return logo_url


def set_enterprise_branding_filter_param(request, provider_id):
    """
    Setting 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS' in session. 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS'
    either be provider_id or ec_uuid. e.g. {provider_id: 'xyz'} or {ec_src: enterprise_customer_uuid}
    """
    ec_uuid = request.GET.get('ec_src', None)
    if provider_id:
        LOGGER.info(
            "Session key 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS' has been set with provider_id '%s'",
            provider_id
        )
        request.session[ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS] = {'provider_id': provider_id}

    elif ec_uuid:
        # we are assuming that none sso based enterprise will return Enterprise Customer uuid as 'ec_src' in query
        # param e.g. edx.org/foo/bar?ec_src=6185ed46-68a4-45d6-8367-96c0bf70d1a6
        LOGGER.info(
            "Session key 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS' has been set with ec_uuid '%s'", ec_uuid
        )
        request.session[ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS] = {'ec_uuid': ec_uuid}


def get_enterprise_branding_filter_param(request):
    """
    :return Filter parameter from session for enterprise customer branding information.

    """
    return request.session.get(ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS, None)
