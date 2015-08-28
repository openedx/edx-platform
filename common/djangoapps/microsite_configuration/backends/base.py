"""
Microsite configuration backend module.

Contains the base class for microsite backends.

"""

from __future__ import absolute_import

import abc


# pylint: disable=unused-argument
class BaseMicrositeBackend(object):
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
        pass

    @abc.abstractmethod
    def get_template_path(self, relative_path, **kwargs):
        """
        Returns a path (string) to a Mako template, which can either be in
        an override or will just return what is passed in which is expected to be a string
        """
        pass

    @abc.abstractmethod
    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        pass

    @abc.abstractmethod
    def get_dict(self, dict_name, default={}, **kwargs):
        """
        Returns a dictionary product of merging the request's microsite and
        the default value.
        This can be used, for example, to return a merged dictonary from the
        settings.FEATURES dict, including values defined at the microsite
        """
        pass

    @abc.abstractmethod
    def is_request_in_microsite(self):
        """
        This will return True/False if the current request is a request within a microsite
        """
        pass

    @abc.abstractmethod
    def has_override_value(self, val_name):
        """
        Returns True/False whether a Microsite has a definition for the
        specified named value
        """
        pass

    @abc.abstractmethod
    def enable_microsites(self, log):
        """
        Enable the use of microsites.
        Used during the startup.py script
        """
        pass

    @abc.abstractmethod
    def get_value_for_org(self, org, val_name, default):
        """
        Returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        pass

    @abc.abstractmethod
    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        pass

    @abc.abstractmethod
    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        pass
