class Registry(object):
    """
    This class implements `Registry` pattern for resolving Entitlements and Scope classes by their string types
    """
    def __init__(self):
        self._scopes = {}
        self._entitlements = {}

    def register_entitlement(self, entitlement_type, class_):
        self._entitlements[entitlement_type] = class_

    def register_scope_strategy(self, scope_type, class_):
        self._scopes[scope_type] = class_

    def get_entitlement_class(self, entitlement_type):
        entitlement_class = self._entitlements.get(entitlement_type)

        if not entitlement_class:
            raise Exception("Unknown entitlement type")

        return entitlement_class

    # TODO: probably there should be get_scope_class method, but so far we're making it without it.


registry = Registry()


def register_entitlement(decorated_class):
    """
    This method is intended to be used as a decorator. It should be applied to a class implementing
    Entitlement interface
    """
    # TODO: should probably check that `decorated_class` is a subclass of `BaseEntitlement`
    registry.register_entitlement(decorated_class.ENTITLEMENT_TYPE, decorated_class)

    return decorated_class


def register_scope(decorated_class):
    """
    This method is intended to be used as a decorator. It should be applied to a class implementing
    Scope inteface
    """
    # TODO: should probably check that `decorated_class` is a subclass of `BaseEntitlement`
    registry.register_scope_strategy(decorated_class.SCOPE_TYPE, decorated_class)

    return decorated_class
