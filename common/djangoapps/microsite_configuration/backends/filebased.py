"""
Microsite backend that reads the configuration from a file

"""
import threading

from django.conf import settings
from microsite_configuration.backends.base import BaseMicrositeBackend


class SettingsFileMicrositeBackend(BaseMicrositeBackend):
    """
    Microsite backend that reads the microsites definitions
    from a dictionary called MICROSITE_CONFIGURATION in the settings file
    """

    def __init__(self, **kwargs):
        super(SettingsFileMicrositeBackend, self).__init__(**kwargs)
        self.current_request_configuration = threading.local()
        self.current_request_configuration.data = {}
        self.current_request_configuration.cache = {}

    def has_configuration_set(self):
        """
        Returns whether there is any Microsite configuration settings
        """
        return getattr(settings, "MICROSITE_CONFIGURATION", False)

    def get_configuration(self):
        """
        Returns the current request's microsite configuration
        """
        if not hasattr(self.current_request_configuration, 'data'):
            return {}

        return self.current_request_configuration.data

    def get_key_from_cache(self, key):
        """
        Retrieves a key from a cache scoped to the thread
        """
        if hasattr(self.current_request_configuration, 'cache'):
            return self.current_request_configuration.cache.get(key)

    def set_key_to_cache(self, key, value):
        """
        Stores a key value pair in a cache scoped to the thread
        """
        if hasattr(self.current_request_configuration, 'cache'):
            self.current_request_configuration.cache[key] = value

    def set_config_by_domain(self, domain):
        """
        For a given request domain, find a match in our microsite configuration
        and then assign it to the thread local in order to make it available
        to the complete Django request processing
        """
        if not self.has_configuration_set() or not domain:
            return

        for key, value in settings.MICROSITE_CONFIGURATION.items():
            subdomain = value.get('domain_prefix')
            if subdomain and domain.startswith(subdomain):
                self._set_microsite_config(key, subdomain, domain)
                return

        # if no match on subdomain then see if there is a 'default' microsite defined
        # if so, then use that
        if 'default' in settings.MICROSITE_CONFIGURATION:
            self._set_microsite_config('default', subdomain, domain)
            return

    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        configuration = self.get_configuration()
        return configuration.get(val_name, default)

    def get_dict(self, dict_name, default={}, **kwargs):
        """
        Returns a dictionary product of merging the request's microsite and
        the default value.
        Supports storing a cache of the merged value to improve performance
        """
        cached_dict = self.get_key_from_cache(dict_name)
        if cached_dict:
            return cached_dict

        output = default.copy()
        output.update(self.get_value(dict_name, {}))

        self.set_key_to_cache(dict_name, output)
        return output

    def is_request_in_microsite(self):
        """
        This will return if current request is a request within a microsite
        """
        return bool(self.get_configuration())

    def has_override_value(self, val_name):
        """
        Will return True/False whether a Microsite has a definition for the
        specified val_name
        """
        configuration = self.get_configuration()
        return val_name in configuration

    def get_all_config(self):
        """
        This returns all configuration for all microsites
        """
        config = {}

        for key, value in settings.MICROSITE_CONFIGURATION.iteritems():
            config[key] = value

        return config

    def _set_microsite_config(self, microsite_config_key, subdomain, domain):
        """
        Helper internal method to actually find the microsite configuration
        """
        config = settings.MICROSITE_CONFIGURATION[microsite_config_key].copy()
        config['subdomain'] = subdomain
        config['microsite_config_key'] = microsite_config_key
        config['site_domain'] = domain

        template_dir = settings.MICROSITE_ROOT_DIR / microsite_config_key / 'templates'
        config['template_dir'] = template_dir
        self.current_request_configuration.data = config

    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        self.current_request_configuration.data = {}
        self.current_request_configuration.cache = {}
