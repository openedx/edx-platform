"""
Features Proxy Implementation
"""
import warnings
from collections.abc import Mapping
from django.utils.functional import LazyObject, empty
from django.conf import settings as django_settings


def ensure_setup(func):
    """Ensure _setup has been called before accessing settings."""
    def wrapper(self, *args, **kwargs):
        if getattr(self, "_wrapped", empty) is empty:
            self._setup()  # pylint: disable=protected-access
        return func(self, *args, **kwargs)
    return wrapper


class FeaturesProxy(LazyObject, Mapping):
    """
    Read-only proxy for Django settings to mimic FEATURES behavior.

    - Lazy loads the Django settings object.
    - Exposes read-only Mapping interface for compatibility.
    - Mutations raise DeprecationWarning.
    """

    def _setup(self):
        self._wrapped = django_settings

    @ensure_setup
    def _get_setting(self, key, default=None):
        return getattr(self._wrapped, key, default)

    def __getitem__(self, key):
        value = self._get_setting(key, empty)
        if value is empty:
            raise KeyError(key)
        return value

    @ensure_setup
    def __contains__(self, key):
        return hasattr(self._wrapped, key)

    @ensure_setup
    def __iter__(self):
        return iter(dir(self._wrapped))

    @ensure_setup
    def __len__(self):
        return len(dir(self._wrapped))

    def get(self, key, default=None):
        value = self._get_setting(key, empty)
        return default if value is empty else value

    @ensure_setup
    def items(self):
        return ((key, self._get_setting(key)) for key in dir(self._wrapped))

    @ensure_setup
    def as_dict(self):
        """Return all settings as a dict."""
        return {key: self._get_setting(key) for key in dir(self._wrapped)}

    def copy(self):
        return self.as_dict()

    def _warn_deprecated(self, key=None, value=None):
        msg = "Modifying FEATURES is deprecated. Use Django settings instead."
        if key is not None:
            msg += f" Tried to modify '{key}'."
        warnings.warn(msg, DeprecationWarning, stacklevel=3)

    def __setitem__(self, key, value):
        self._warn_deprecated(key, value)

    def __delitem__(self, key):
        self._warn_deprecated(key)

    def update(self, *args, **kwargs):
        self._warn_deprecated()
