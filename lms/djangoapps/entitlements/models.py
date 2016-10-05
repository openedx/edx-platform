from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from .registry import registry
from .scope import ScopeFactory


class EntitlementModel(models.Model):
    type = models.CharField(
        max_length=255, help_text=_("Entitlement type")
    )
    scope_id = models.CharField(max_length=4000, help_text=_("ID of an object Entitlement is scoped to"))
    parameters = JSONField(blank=True, default={})

    class Meta(object):
        app_label = "entitlements"

    def get_entitlement(self):
        entitlement_class = registry.get_entitlement_and_scope(self.type)
        scope_strategy = ScopeFactory.make_scope_strategy(entitlement_class.SCOPE_TYPE)
        return entitlement_class(self.scope_id, scope_strategy, **self.parameters)


class EntitlementGroup(models.Model):
    ENTERPRISE_CUSTOMER = "enterprise_customer"

    name = models.CharField(max_length=255, help_text=_("Name of the group"))
    kind = models.CharField(
        max_length=50,
        choices=(
            (ENTERPRISE_CUSTOMER, _("Enterprise Customer")),
        )
    )
    entitlements = models.ManyToManyField(EntitlementModel)
    users = models.ManyToManyField(User, related_name='entitlement_groups', blank=True)

    class Meta(object):
        app_label = "entitlements"
