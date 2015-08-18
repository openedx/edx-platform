"""
Microsite backend that reads the configuration from the database

"""
import os.path
import threading
import edxmako
import json

from django.conf import settings
from microsite_configuration.backends.base import BaseMicrositeBackend
from microsite_configuration.models import Microsite


class DatabaseMicrositeBackend(BaseMicrositeBackend):
    """
    Microsite backend that reads the microsites definitions
    from a table in the database according to the models.py file
    """

    def __init__(self, **kwargs):
        super(DatabaseMicrositeBackend, self).__init__(**kwargs)
        self.current_request_configuration = threading.local()
        self.current_request_configuration.data = {}

    def has_configuration_set(self):
        """
        Returns whether there is any Microsite configuration settings
        """
        if Microsite.objects.count():
            return True
        else:
            return False

    def get_configuration(self):
        """
        Returns the current request's microsite configuration
        """
        if not hasattr(self.current_request_configuration, 'data'):
            return {}

        return self.current_request_configuration.data

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

    def get_template_path(self, relative_path, **kwargs):
        """
        Returns a path (string) to a Mako template, which can either be in
        a microsite directory (as an override) or will just return what is passed in which is
        expected to be a string
        """

        if not self.is_request_in_microsite():
            return relative_path

        microsite_template_path = str(self.get_value('template_dir', None))

        if microsite_template_path:
            search_path = os.path.join(microsite_template_path, relative_path)

            if os.path.isfile(search_path):
                path = '/{0}/templates/{1}'.format(
                    self.get_value('microsite_name'),
                    relative_path
                )
                return path

        return relative_path

    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        configuration = self.get_configuration()
        return configuration.get(val_name, default)

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

    def enable_microsites(self, log):
        """
        Enable the use of microsites, from a dynamic defined list in the db
        """
        if not settings.FEATURES['USE_MICROSITES']:
            return

        microsites_root = settings.MICROSITE_ROOT_DIR

        if microsites_root.isdir():
            settings.TEMPLATE_DIRS.append(microsites_root)
            edxmako.paths.add_lookup('main', microsites_root)
            settings.STATICFILES_DIRS.insert(0, microsites_root)

            log.info('Loading microsite path at %s', microsites_root)
        else:
            log.error(
                'Error loading %s. Directory does not exist',
                microsites_root
            )

    def get_value_for_org(self, org, val_name, default):
        """
        Returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        if not self.has_configuration_set():
            return default

        # Filter at the db
        candidates = Microsite.objects.all()
        for microsite in candidates:
            current = json.loads(microsite.values)
            org_filter = current.get('course_org_filter')
            if org_filter:
                return current.get(val_name, default)

        return default

    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        org_filter_set = set()
        if not self.has_configuration_set():
            return org_filter_set

        # Get the orgs in the db
        candidates = Microsite.objects.all()
        for microsite in candidates:
            current = json.loads(microsite.values)
            org_filter = current.get('course_org_filter')
            if org_filter:
                org_filter_set.add(org_filter)

        return org_filter_set

    def _set_microsite_config_from_obj(self, subdomain, domain, microsite_object):
        """
        Helper internal method to actually find the microsite configuration
        """
        config = microsite_object.copy()
        config['subdomain'] = subdomain
        config['site_domain'] = domain
        self.current_request_configuration.data = config

    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        self.current_request_configuration.data = {}
