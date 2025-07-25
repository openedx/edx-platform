"""
Features Dictionary Flattening Proxy
"""

import warnings
from django.conf import settings


class FeaturesProxy(dict):
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

    def __init__(self, namespace):
        """Store the namespace (as a dict)"""
        self.ns = namespace

    def __getitem__(self, key):
        """Retrieve a feature flag by key"""
        return self.ns[key]

    def __setitem__(self, key, value):
        """Warn users that FEATURES is deprecated as a dict"""
        warnings.warn(
            f"Accessing FEATURES as a dict is deprecated. "
            f"Use direct settings override: settings.{key} = {value!r}",
            DeprecationWarning,
            stacklevel=2
        )
        # Set the feature and sync to Django settings
        self.ns[key] = value
        self._update_django_settings(key, value)

    def __delitem__(self, key):
        """Delete the feature and remove from Django settings"""
        del self.ns[key]
        self._remove_from_django_settings(key)

    def __iter__(self):
        return iter(self.ns)

    def __len__(self):
        return len(self.ns)

    def __contains__(self, key):
        return key in self.ns

    def to_dict(self):
        return dict(self.ns)

    def get(self, key, default=None):
        """Standard dict-style get with default"""
        return self.ns.get(key, default)

    def update(self, *args, **kwargs):
        """
        Update multiple features at once.

        Examples:
            proxy.update({'FEATURE_A': True})
            proxy.update(FEATURE_B=False)
        """
        for mapping in args:
            for key, value in mapping.items():
                self[key] = value  # uses __setitem__
        for key, value in kwargs.items():
            self[key] = value  # uses __setitem__

    def copy(self):
        """
        Return a shallow copy of the underlying namespace wrapped in a new FeaturesProxy.
        """
        return FeaturesProxy(self.ns.copy())

    def _update_django_settings(self, key, value):
        """
        Attempt to reflect the updated feature flag in django.conf.settings.
        """
        try:
            setattr(settings, key, value)

            # Edge case: Also update wrapped settings object for some test cases
            if hasattr(settings, '_wrapped'):
                wrapped = settings._wrapped      # pylint: disable=protected-access
                setattr(wrapped, key, value)
                if hasattr(wrapped, '__dict__'):
                    wrapped.__dict__[key] = value

        except (AttributeError, TypeError) as e:
            warnings.warn(f"Failed to update Django settings for key {key}: {e}")

    def _remove_from_django_settings(self, key):
        """
        Remove the key from django.conf.settings and its internal structures.
        """
        try:
            for target in (settings, getattr(settings, '_wrapped', None)):
                if target and hasattr(target, key):
                    delattr(target, key)
                if target and hasattr(target, '__dict__'):
                    target.__dict__.pop(key, None)
        except (AttributeError, TypeError) as e:
            warnings.warn(f"Failed to delete Django settings for key {key}: {e}")
