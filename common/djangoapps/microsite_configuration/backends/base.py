"""
Microsite configuration backend module.

Contains the base classes for microsite backends.

AbstractBaseMicrositeBackend is Abstract Base Class for the microsite configuration backend.
BaseMicrositeBackend is Base Class for microsite configuration backend.
BaseMicrositeTemplateBackend is Base Class for the microsite template backend.
"""

from __future__ import absolute_import

import abc
import edxmako
import os.path
import threading

from django.conf import settings

from util.url import strip_port_from_host


# pylint: disable=unused-argument
class AbstractBaseMicrositeBackend(object):
    """
    Abstract Base Class for the microsite backends.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def set_config_by_domain(self, domain):
        """
        For a given request domain, find a match in our microsite configuration
        and make it available to the complete django request process
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_dict(self, dict_name, default=None, **kwargs):
        """
        Returns a dictionary product of merging the request's microsite and
        the default value.
        This can be used, for example, to return a merged dictonary from the
        settings.FEATURES dict, including values defined at the microsite
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def is_request_in_microsite(self):
        """
        This will return True/False if the current request is a request within a microsite
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def has_override_value(self, val_name):
        """
        Returns True/False whether a Microsite has a definition for the
        specified named value
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_config(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_value_for_org(self, org, val_name, default=None):
        """
        This returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within a microsite. This can be used,
        for example, to do filtering
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        raise NotImplementedError()


class BaseMicrositeBackend(AbstractBaseMicrositeBackend):
    """
    Base class for Microsite backends.
    """

    def __init__(self, **kwargs):
        super(BaseMicrositeBackend, self).__init__(**kwargs)
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
        Returns the current request's microsite configuration.
        if request's microsite configuration is not present returns empty dict.
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

    def get_dict(self, dict_name, default=None, **kwargs):
        """
        Returns a dictionary product of merging the request's microsite and
        the default value.
        Supports storing a cache of the merged value to improve performance
        """
        cached_dict = self.get_key_from_cache(dict_name)
        if cached_dict:
            return cached_dict

        default = default or {}
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

    def get_value_for_org(self, org, val_name, default=None):
        """
        This returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """

        if not self.has_configuration_set():
            return default

        # Filter at the setting file
        for value in settings.MICROSITE_CONFIGURATION.itervalues():
            org_filter = value.get('course_org_filter', None)
            if org_filter == org:
                return value.get(val_name, default)
        return default

    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within a microsite. This can be used,
        for example, to do filtering
        """
        org_filter_set = set()

        if not self.has_configuration_set():
            return org_filter_set

        # Get the orgs in the db
        for microsite in settings.MICROSITE_CONFIGURATION.itervalues():
            org_filter = microsite.get('course_org_filter')
            if org_filter:
                org_filter_set.add(org_filter)

        return org_filter_set

    def _set_microsite_config(self, microsite_config_key, subdomain, domain):
        """
        Helper internal method to actually find the microsite configuration
        """
        config = settings.MICROSITE_CONFIGURATION[microsite_config_key].copy()
        config['subdomain'] = strip_port_from_host(subdomain)
        config['microsite_config_key'] = microsite_config_key
        config['site_domain'] = strip_port_from_host(domain)

        template_dir = settings.MICROSITE_ROOT_DIR / microsite_config_key / 'templates'
        config['template_dir'] = template_dir
        self.current_request_configuration.data = config

    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        self.current_request_configuration.data = {}
        self.current_request_configuration.cache = {}

    def enable_microsites(self, log):
        """
        Configure the paths for the microsites feature
        """
        microsites_root = settings.MICROSITE_ROOT_DIR

        if os.path.isdir(microsites_root):
            edxmako.paths.add_lookup('main', microsites_root)
            settings.STATICFILES_DIRS.insert(0, microsites_root)

            log.info('Loading microsite path at %s', microsites_root)
        else:
            log.error(
                'Error loading %s. Directory does not exist',
                microsites_root
            )

    def enable_microsites_pre_startup(self, log):
        """
        The TEMPLATE_ENGINE directory to search for microsite templates
        in non-mako templates must be loaded before the django startup
        """
        microsites_root = settings.MICROSITE_ROOT_DIR
        microsite_config_dict = settings.MICROSITE_CONFIGURATION

        if microsite_config_dict:
            settings.DEFAULT_TEMPLATE_ENGINE['DIRS'].append(microsites_root)


class BaseMicrositeTemplateBackend(object):
    """
    Interface for microsite template providers. Base implementation is to use the filesystem.
    When this backend is used templates are first searched in location set in `template_dir`
    configuration of microsite on filesystem.
    """

    def get_template_path(self, relative_path, **kwargs):
        """
        Returns a path (string) to a Mako template, which can either be in
        an override or will just return what is passed in which is expected to be a string
        """

        from microsite_configuration.microsite import get_value as microsite_get_value

        microsite_template_path = microsite_get_value('template_dir', None)

        if not microsite_template_path:
            microsite_template_path = '/'.join([
                settings.MICROSITE_ROOT_DIR,
                microsite_get_value('microsite_config_key', 'default'),
                'templates',
            ])

        search_path = os.path.join(microsite_template_path, relative_path)
        if os.path.isfile(search_path):
            path = '/{0}/templates/{1}'.format(
                microsite_get_value('microsite_config_key'),
                relative_path
            )
            return path
        else:
            return relative_path

    def get_template(self, uri):
        """
        Returns the actual template for the microsite with the specified URI,
        default implementation returns None, which means that the caller framework
        should use default behavior
        """

        return
