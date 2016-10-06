"""
This module contains hooks into other workflows found across LMS
"""
from django.db import transaction
from social.pipeline import partial
from third_party_auth import provider

from entitlements.scope import ScopeFactory
from .enterprise_entitlements import ShareResultsEntitlement
from .models import EnterpriseCustomer


@partial.partial
def sso_login_hook(backend=None, user=None, **kwargs):
    """
    Hooks into SSO login workflow to perform linked user to an EnterpriseCustomer by adding it to corresponding
    Entitlement group. It is added to third_party_auth AUTHENTICATION_PIPELINE
    :param backend: authentication backend
    :param django.contrib.auth.models.User user: current user
    :param dict kwargs: other parameters
    :return: None
    """
    # get current provider slug ...
    current_provider = provider.Registry.get_from_pipeline({'backend': backend.name, 'kwargs': kwargs})
    provider_slug = current_provider.idp_slug

    try:
        # ... to check it against all enterprise customer linked providers field
        # TODO: Obviously, fetches quite a lot of data from DB and than iterates over it.
        # linear worst-case performance, where N = total number of enterprise customers
        # also provider_slug in enterprise_customer.third_party_providers might be linear too.
        all_enterprise_customers = EnterpriseCustomer.objects.all()
        matching_enterprise_customer = next(
            enterprise_customer for enterprise_customer in all_enterprise_customers
            if provider_slug in enterprise_customer.third_party_providers
        )
    except StopIteration:
        matching_enterprise_customer = None

    if matching_enterprise_customer:
        # ... and add it to a matching enterprise customer if found
        matching_enterprise_customer.entitlement_group.users.add(user)
        create_data_sharing_consent_entitlement(user, matching_enterprise_customer.entitlement_group)
    else:
        # ... and just do nothing if not found any
        pass


@transaction.atomic
def create_data_sharing_consent_entitlement(user, entitlement_group):
    # TODO: EntitlementFactory to avoid creating strategy and passing it directly?
    scope_strategy = ScopeFactory.make_scope_strategy(ShareResultsEntitlement.SCOPE_TYPE)
    entitlement = ShareResultsEntitlement(user.id, scope_strategy)

    entitlement_model = entitlement.save()
    entitlement_group.entitlements.add(entitlement_model)
    entitlement_group.save()
