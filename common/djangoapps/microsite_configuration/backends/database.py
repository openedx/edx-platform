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

        # CDODGE: I believe this will be called on every request into edx-platform
        # so it seems more expensive than it should be. Like set_config_by_domain
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

        # CDODGE: I'm concerned about this performance. Seems like we should cache this mapping
        # and maybe auto expire the cache extry after 5 minutes. This method will be called on
        # every request into edx-platform
        candidates = Microsite.objects.all()
        for microsite in candidates:
            subdomain = microsite.subdomain
            if subdomain and domain.startswith(subdomain):
                self._set_microsite_config_from_obj(subdomain, domain, microsite)
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
        config = json.loads(microsite_object.values)
        config['subdomain'] = subdomain
        config['site_domain'] = domain
        config['microsite_config_key'] = microsite_object.key
        self.current_request_configuration.data = config
