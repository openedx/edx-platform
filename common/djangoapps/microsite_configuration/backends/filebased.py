"""
Microsite backend that reads the configuration from a file

"""
import os.path
import threading
import edxmako

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

    def enable_microsites(self, log):
        """
        Enable the use of microsites, which are websites that allow
        for subdomains for the edX platform, e.g. foo.edx.org
        """

        microsites_root = settings.MICROSITE_ROOT_DIR
        microsite_config_dict = settings.MICROSITE_CONFIGURATION

        for ms_name, ms_config in microsite_config_dict.items():
            # Calculate the location of the microsite's files
            ms_root = microsites_root / ms_name
            ms_config = microsite_config_dict[ms_name]

            # pull in configuration information from each
            # microsite root

            if ms_root.isdir():
                # store the path on disk for later use
                ms_config['microsite_root'] = ms_root

                template_dir = ms_root / 'templates'
                ms_config['template_dir'] = template_dir

                ms_config['microsite_name'] = ms_name
                log.info('Loading microsite %s', ms_root)
            else:
                # not sure if we have application logging at this stage of
                # startup
                log.error('Error loading microsite %s. Directory does not exist', ms_root)
                # remove from our configuration as it is not valid
                del microsite_config_dict[ms_name]

        # if we have any valid microsites defined, let's wire in the Mako and STATIC_FILES search paths
        if microsite_config_dict:
            settings.TEMPLATE_DIRS.append(microsites_root)
            edxmako.paths.add_lookup('main', microsites_root)

            settings.STATICFILES_DIRS.insert(0, microsites_root)

    def get_value_for_org(self, org, val_name, default):
        """
        Returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        if not self.has_configuration_set():
            return default

        # Filter at the setting file
        for value in settings.MICROSITE_CONFIGURATION.values():
            org_filter = value.get('course_org_filter', None)
            if org_filter == org:
                return value.get(val_name, default)
        return default

    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        org_filter_set = set()
        if not self.has_configuration_set():
            return org_filter_set

        # Get the orgs in the settings file
        for value in settings.MICROSITE_CONFIGURATION.values():
            org_filter = value.get('course_org_filter')
            if org_filter:
                org_filter_set.add(org_filter)

        return org_filter_set

    def _set_microsite_config(self, microsite_config_key, subdomain, domain):
        """
        Helper internal method to actually find the microsite configuration
        """
        config = settings.MICROSITE_CONFIGURATION[microsite_config_key].copy()
        config['subdomain'] = subdomain
        config['microsite_config_key'] = microsite_config_key
        config['site_domain'] = domain
        self.current_request_configuration.data = config

    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        self.current_request_configuration.data = {}
        self.current_request_configuration.cache = {}
