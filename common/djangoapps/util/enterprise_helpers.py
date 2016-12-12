"""
Helpers to access the enterprise app
"""
from django.conf import settings
from django.utils.translation import ugettext as _

try:
    from enterprise.models import EnterpriseCustomer
    from enterprise.tpa_pipeline import (
        active_provider_requests_data_sharing,
        active_provider_enforces_data_sharing,
        get_enterprise_customer_for_request,
    )

except ImportError:
    pass

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


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
