"""
This module contains generic Entitlement functionality.

Metaentitlements (entitlements to manage entitlements) should probably be added here (when a need for the arise).
"""
from .scope import ScopeFactory
from .registry import registry
from .models import EntitlementModel


class BaseEntitlement(object):
    """
    This is an (abstract) base class for Entitlements.
    """
    ENTITLEMENT_TYPE = None
    SCOPE_TYPE = None

    def __init__(self, scope_id, scope_strategy, **kwargs):
        assert(scope_strategy.SCOPE_TYPE == self.SCOPE_TYPE)
        self._scope_id = scope_id
        self._scope_strategy = scope_strategy

    @property
    def scope(self):
        """
        Returns scope of this entitlement
        """
        return self._scope_strategy.get_scope(self._scope_id)

    def save(self):
        """
        Creates or updates EntitlementModel instance
        :return:
        """
        # FIXME: different EntitlementGroups might contain different Entitlements of the same type and scope, but with
        # different parameters - should probably keep track of actual entitlement model ID and use it insted type and
        # scope_id as "primary key"
        entitlement_model, unused_created = EntitlementModel.objects.update_or_create(
            type=self.ENTITLEMENT_TYPE,
            scope_id=self._scope_id,
        )
        entitlement_model.parameters = self._get_model_parameters()
        entitlement_model.save()
        return entitlement_model

    def _get_model_parameters(self):
        """
        Returns Entitlement parameters to be stored in `parameters` field on entitlement model
        :return: dictionary
        """
        return {}

    def is_applicable_to(self, target):
        """
        Checks if `target` matches the scope of this entitlement.
        :param object target: an opbject to check entitlement scope.
        :return: boolean
        """
        return self.scope == target


class EntitlementFactory(object):
    def __init__(self, scope_factory):
        self._scope_factory = scope_factory

    def build_entitlement_from_model(self, entitlement_model):
        """
        This method performs instantiation of Entitlement represented by entitlement model
        :return: instance of BaseEntitlement
        """
        entitlement_class = registry.get_entitlement_class(entitlement_model.type)
        scope_strategy = self._scope_factory.make_scope_strategy(entitlement_class.SCOPE_TYPE)
        return entitlement_class(entitlement_model.scope_id, scope_strategy, **entitlement_model.parameters)

    def build_entitlement(self, type, scope_id, parameters):
        entitlement_class = registry.get_entitlement_class(type)
        entitlement_class(scope_id, **parameters)
        return entitlement_class

entitlement_factory = EntitlementFactory(ScopeFactory)

