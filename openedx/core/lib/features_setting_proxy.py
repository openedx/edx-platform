"""
Features Dictionary Flattening Proxy
"""


import warnings
from collections.abc import MutableMapping

class FeaturesProxy(MutableMapping):
    """
    A proxy for feature flags stored in the settings namespace.

    Features:
    - Flattens features from configuration (e.g., YAML or env) into the local settings namespace.
    - Automatically updates `django.conf.settings` when a feature is modified.
    - Acts like a dict (get, set, update, etc.).

    Example usage:
        fp = FeaturesProxy(LocalNamespace)
        fp["NEW_FEATURE"] = True
        val = fp.get("EXISTING_FLAG", False)
    """

    def __init__(self, namespace=None):
        """Store the namespace (as a dict)"""
        if namespace is None:
            namespace = {}
        self.ns = namespace.copy()
        # print(f"DEBUG PROXY SETTINGS TOTAL: {len(self)}")

    def __getitem__(self, key):
        """Retrieve a feature flag by key"""
        return self.ns[key]

    def __setitem__(self, key, value):
        """Warn users that FEATURES is deprecated as a dict"""
        warnings.warn(
            f"Accessing FEATURES as a dict is deprecated. "
            f"Add '{key} = {value!r}' to your Django settings module instead of modifying FEATURES.",
            DeprecationWarning,
            stacklevel=2
        )
        self.ns[key] = value

    def __delitem__(self, key):
        """Delete the feature and remove from Django settings"""
        del self.ns[key]

    def __iter__(self):
        return iter(self.ns)

    def __len__(self):
        return len(self.ns)

    def __contains__(self, key):
        return key in self.ns

    def clear(self):
        self.ns.clear()

    def to_dict(self):
        return dict(self.ns)

    def get(self, key, default=None):
        """Standard dict-style get with default"""
        return self.ns.get(key, default)

    def update(self, *args, **kwargs):    # pylint: disable=arguments-differ
        """
        Update multiple features at once.

        Examples:
            proxy.update({'FEATURE_A': True})
            proxy.update(FEATURE_B=False)
        """
        for mapping in args:
            if hasattr(mapping, 'items'):
                for key, value in mapping.items():
                    self[key] = value
            else:
                for key, value in mapping:
                    self[key] = value
        for key, value in kwargs.items():
            self[key] = value

    def copy(self):
        """
        Return a shallow copy of the underlying namespace wrapped in a new FeaturesProxy.
        """
        return FeaturesProxy(self.ns.copy())
