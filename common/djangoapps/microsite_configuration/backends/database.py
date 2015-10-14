"""
Microsite backend that reads the configuration from the database

"""
import json

from microsite_configuration.backends.filebased import SettingsFileMicrositeBackend
from microsite_configuration.models import Microsite


class DatabaseMicrositeBackend(SettingsFileMicrositeBackend):
    """
    Microsite backend that reads the microsites definitions
    from a table in the database according to the models.py file
    """

    def has_configuration_set(self):
        """
        Returns whether there is any Microsite configuration settings
        """
        if Microsite.objects.count():
            return True
        else:
            return False

    def set_config_by_domain(self, domain):
        """
        For a given request domain, find a match in our microsite configuration
        and then assign it to the thread local in order to make it available
        to the complete Django request processing
        """
        if not self.has_configuration_set() or not domain:
            return

        candidates = Microsite.objects.all()
        for microsite in candidates:
            subdomain = microsite.subdomain
            if subdomain and domain.startswith(subdomain):
                values = json.loads(microsite.values)
                self._set_microsite_config_from_obj(subdomain, domain, values)
                return

        # if no match on subdomain then see if there is a 'default' microsite
        # defined in the db. If so, then use it
        try:
            microsite = Microsite.objects.get(key='default')
            values = json.loads(microsite.values)
            self._set_microsite_config_from_obj(subdomain, domain, values)
            return
        except Microsite.DoesNotExist:
            return

    def get_all_config(self):
        """
        This returns all configuration for all microsites
        """
        config = {}

        candidates = Microsite.objects.all()
        for microsite in candidates:
            values = json.loads(microsite.values)
            config[microsite.key] = values

        return config

    def _set_microsite_config_from_obj(self, subdomain, domain, microsite_object):
        """
        Helper internal method to actually find the microsite configuration
        """
        config = microsite_object.copy()
        config['subdomain'] = subdomain
        config['site_domain'] = domain
        config['microsite_config_key'] = microsite_object.key
        self.current_request_configuration.data = config
