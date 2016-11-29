"""
Helpers to access the enterprise app
"""
from django.conf import settings
from django.utils.translation import ugettext as _
import logging

try:
    from enterprise.models import EnterpriseCustomer
    from enterprise import api as enterprise_api
    from enterprise.tpa_pipeline import (
        active_provider_requests_data_sharing,
        active_provider_enforces_data_sharing,
        get_enterprise_customer_for_request,
    )

except ImportError:
    pass

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS = 'enterprise_customer_branding_override_details'
LOGGER = logging.getLogger("edx.enterprise_helpers")


def enterprise_enabled():
    """
    Determines whether the Enterprise app is installed
    """
    return 'enterprise' in settings.INSTALLED_APPS


def data_sharing_consent_requested(request):
    """
    Determine if the EnterpriseCustomer for a given HTTP request
    requests data sharing consent
    """
    if not enterprise_enabled():
        return False
    return active_provider_requests_data_sharing(request)


def data_sharing_consent_required_at_login(request):
    """
    Determines if data sharing consent is required at
    a given location
    """
    if not enterprise_enabled():
        return False
    return active_provider_enforces_data_sharing(request, EnterpriseCustomer.AT_LOGIN)


def data_sharing_consent_requirement_at_login(request):
    """
    Returns either 'optional' or 'required' based on where we are.
    """
    if not enterprise_enabled():
        return None
    if data_sharing_consent_required_at_login(request):
        return 'required'
    if data_sharing_consent_requested(request):
        return 'optional'
    return None


def insert_enterprise_fields(request, form_desc):
    """
    Enterprise methods which modify the logistration form are called from this method.
    """
    if not enterprise_enabled():
        return
    add_data_sharing_consent_field(request, form_desc)


def add_data_sharing_consent_field(request, form_desc):
    """
    Adds a checkbox field to be selected if the user consents to share data with
    the EnterpriseCustomer attached to the SSO provider with which they're authenticating.
    """
    enterprise_customer = get_enterprise_customer_for_request(request)
    required = data_sharing_consent_required_at_login(request)

    if not data_sharing_consent_requested(request):
        return

    label = _(
        "I agree to allow {platform_name} to share data about my enrollment, "
        "completion and performance in all {platform_name} courses and programs "
        "where my enrollment is sponsored by {ec_name}."
    ).format(
        platform_name=configuration_helpers.get_value("PLATFORM_NAME", settings.PLATFORM_NAME),
        ec_name=enterprise_customer.name
    )

    error_msg = _(
        "To link your account with {ec_name}, you are required to consent to data sharing."
    ).format(
        ec_name=enterprise_customer.name
    )

    form_desc.add_field(
        "data_sharing_consent",
        label=label,
        field_type="checkbox",
        default=False,
        required=required,
        error_messages={"required": error_msg},
    )


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
        branding_info = enterprise_api.get_enterprise_branding_info_by_provider_id(provider_id=provider_id)
    elif ec_uuid:
        branding_info = enterprise_api.get_enterprise_branding_info_by_ec_uuid(ec_uuid=ec_uuid)

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
