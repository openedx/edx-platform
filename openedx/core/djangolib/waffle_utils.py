"""
Utilities for waffle usage.
"""
from abc import ABCMeta
from contextlib import contextmanager
import logging

from waffle.testutils import override_switch as waffle_override_switch
from waffle import switch_is_active

from request_cache import get_cache as get_request_cache


log = logging.getLogger(__name__)


class WafflePlus(object):
    """
    Waffle helper class that provides native support for
    namespacing waffle settings and caching within a request.
    """
    __metaclass__ = ABCMeta

    def __init__(self, namespace, log_prefix=None):
        self.namespace = namespace
        self.log_prefix = log_prefix

    def _namespaced_setting_name(self, setting_name):
        """
        Returns the namespaced name of the waffle switch/flag.
        """
        assert self.namespace is not None
        return u'{}.{}'.format(self.namespace, setting_name)

    @staticmethod
    def _get_request_cache():
        """
        Returns the request cache used by WafflePlus classes.
        """
        return get_request_cache('WafflePlus')


class WaffleSwitchPlus(WafflePlus):
    """
    Waffle Switch helper class that provides native support for
    namespacing waffle switches and caching within a request.
    """
    def is_enabled(self, switch_name):
        """
        Returns and caches whether the given waffle switch is enabled.
        """
        namespaced_switch_name = self._namespaced_setting_name(switch_name)
        value = self._cached_switches.get(namespaced_switch_name)
        if value is None:
            value = switch_is_active(namespaced_switch_name)
            self._cached_switches[namespaced_switch_name] = value
        return value

    @contextmanager
    def override(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the request cache AND in the model.
        """
        previous_active = self.is_enabled(switch_name)
        try:
            self.override_for_request(switch_name, active)
            with self.override_in_model(switch_name, active):
                yield
        finally:
            self.override_for_request(switch_name, previous_active)

    def override_for_request(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the remainder of
        this request (as this is not a context manager).
        Note: The value is overridden in the request cache, not in the model.
        """
        namespaced_switch_name = self._namespaced_setting_name(switch_name)
        self._cached_switches[namespaced_switch_name] = active
        log.info(u"%sSwitch '%s' set to %s for request.", self.log_prefix, namespaced_switch_name, active)

    @contextmanager
    def override_in_model(self, switch_name, active=True):
        """
        Overrides the active value for the given switch for the duration of this
        contextmanager.
        Note: The value is overridden in the model, not the request cache.
        """
        namespaced_switch_name = self._namespaced_setting_name(switch_name)
        with waffle_override_switch(namespaced_switch_name, active):
            log.info(u"%sSwitch '%s' set to %s in model.", self.log_prefix, namespaced_switch_name, active)
            yield

    @property
    def _cached_switches(self):
        """
        Returns cached active values of all switches in this namespace.
        """
        return self._all_cached_switches.setdefault(self.namespace, {})

    @property
    def _all_cached_switches(self):
        """
        Returns dictionary of all switches in the request cache,
        keyed by namespace.
        """
        return self._get_request_cache().setdefault('switches', {})
