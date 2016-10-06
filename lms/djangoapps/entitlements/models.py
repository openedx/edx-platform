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

    def __unicode__(self):
        return u"Entitlement type: {type}, scope_id: {scope_id}".format(type=self.type, scope_id=self.scope_id)


class EntitlementGroup(models.Model):
    name = models.CharField(max_length=255, help_text=_("Name of the group"))
    entitlements = models.ManyToManyField(EntitlementModel)
    users = models.ManyToManyField(User, related_name='entitlement_groups', blank=True)

    class Meta(object):
        app_label = "entitlements"

    def get_entitlement_models_of_type(self, entitlement_type):
        for entitlement_model in self.entitlements.all():
            if entitlement_model.type == entitlement_type:
                yield entitlement_model

    def __unicode__(self):
        return u"EntitlementGroup {name} (id: {id})".format(name=self.name, id=self.pk)