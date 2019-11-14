"""
Pipeline for the SAML Enterprise feature.

The Enterprise feature must be turned on for this pipeline to have any effect.
"""

from __future__ import absolute_import
from openedx.features.enterprise_support.api import (
    EnterpriseApiClient,
    enterprise_is_enabled,
    get_enterprise_learner_data,
    get_enterprise_customer_from_session,
    activate_learner_enterprise
)
from openedx.core.djangoapps.user_api.accounts.utils import is_multiple_user_enterprises_feature_enabled
from third_party_auth.utils import is_provider_saml, saml_idp_name


@enterprise_is_enabled()
def set_learner_active_enterprise(user=None, backend=None, strategy=None, **kwargs):
    """
    Make 'active' a user's enterprise,
    if the currently 'active' enterprise in EnterpriseCustomerUser does not match the SAML idp-enterprise
    """
    if is_multiple_user_enterprises_feature_enabled() and is_provider_saml(backend.name, kwargs):
        request = strategy.request
        idp_name = saml_idp_name(backend.name, kwargs['response']['idp_name'])
        enterprise_customer = get_enterprise_customer_from_session(request)
        if not enterprise_customer or idp_name != enterprise_customer['identity_provider']:
            learner_enterprises = get_enterprise_learner_data(user)

            if len(learner_enterprises) > 1:
                # Check and change the active enterprise_customer only if user is associated to multiple enterprises.
                idp_enterprise = [learner_enterprise['enterprise_customer'] for learner_enterprise
                                  in learner_enterprises if
                                  learner_enterprise['enterprise_customer']['identity_provider'] == idp_name]
                if idp_enterprise:
                    uuid = idp_enterprise[0]['uuid']
                    enterprise_status_changed = EnterpriseApiClient(user=user).post_active_enterprise_customer(
                        user.username, uuid, True)
                    if enterprise_status_changed:
                        activate_learner_enterprise(request, idp_enterprise[0])
    return None
