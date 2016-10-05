class Registry(object):
    def __init__(self):
        self._scopes = {}
        self._entitlements = {}

    def register_entitlement(self, entitlement_type, class_):
        self._entitlements[entitlement_type] = class_

    def register_scope_strategy(self, scope_type, class_):
        self._scopes[scope_type] = class_

    def get_entitlement_and_scope(self, entitlement_type):
        entitlement_class = self._entitlements.get(entitlement_type)

        if not entitlement_class:
            raise Exception("Unknown entitlement type")

        return entitlement_class


registry = Registry()


def register_entitlement(decorated_class):
    registry.register_entitlement(decorated_class.ENTITLEMENT_TYPE, decorated_class)

    return decorated_class


def register_scope(decorated_class):
    registry.register_scope_strategy(decorated_class.SCOPE_TYPE, decorated_class)

    return decorated_class
