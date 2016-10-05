from django.db import transaction
from social.pipeline import partial
from third_party_auth import provider

from entitlements.scope import ScopeFactory
from .enterprise_entitlements import ShareResultsEntitlement
from .models import EnterpriseCustomer


@partial.partial
def sso_login_hook(backend=None, user=None, **kwargs):
    current_provider = provider.Registry.get_from_pipeline({'backend': backend.name, 'kwargs': kwargs})
    provider_slug = current_provider.idp_slug

    all_enterprise_customers = EnterpriseCustomer.objects.all()
    matching_enterprise_customer = next(
        enterprise_customer for enterprise_customer in all_enterprise_customers
        if provider_slug in enterprise_customer.third_party_providers
    )

    matching_enterprise_customer.entitlement_group.users.add(user)
    create_data_sharing_consent_entitlement(user, matching_enterprise_customer.entitlement_group)


@transaction.atomic
def create_data_sharing_consent_entitlement(user, entitlement_group):
    scope_strategy = ScopeFactory.make_scope_strategy(ShareResultsEntitlement.SCOPE_TYPE)
    entitlement = ShareResultsEntitlement(user.id, scope_strategy)
    entitlement_model = entitlement.save()
    entitlement_group.entitlements.add(entitlement_model)
    entitlement_group.save()
