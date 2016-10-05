from django.db import models
from django.utils.translation import ugettext_lazy as _

from entitlements.models import EntitlementGroup


class EnterpriseCustomer(models.Model):
    name = models.CharField(max_length=255)
    entitlement_group = models.OneToOneField(EntitlementGroup, related_name="enterprise_customer")
    linked_third_party_providers = models.CharField(
        max_length=4000, blank=True, help_text=_("Comma-separated list of TPA IdP slugs")
    )

    @property
    def third_party_providers(self):
        return [slug.strip() for slug in self.linked_third_party_providers.split(",")]

