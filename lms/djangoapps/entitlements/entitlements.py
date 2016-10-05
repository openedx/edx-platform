from .models import EntitlementModel


class BaseEntitlement(object):
    ENTITLEMENT_TYPE = None
    SCOPE_TYPE = None

    def __init__(self, scope_id, scope_strategy, **kwargs):
        assert(scope_strategy.SCOPE_TYPE == self.SCOPE_TYPE)
        self._scope_id = scope_id
        self._scope_strategy = scope_strategy

    @property
    def scope(self):
        return self._scope_strategy.get_scope(self._scope_id)

    def save(self):
        entitlement_model, unused_created = EntitlementModel.objects.update_or_create(
            type=self.ENTITLEMENT_TYPE,
            scope_id=self._scope_id,
        )
        entitlement_model.parameters = self._get_model_parameters()
        entitlement_model.save()
        return entitlement_model

    def _get_model_parameters(self):
        return {}

    def applicable_to(self, target):
        return self.scope == target

