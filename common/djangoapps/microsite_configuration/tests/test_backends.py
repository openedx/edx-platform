# -*- coding: utf-8 -*-
"""
Test Microsite backends.
"""

import logging
from mock import patch
from django.test import TestCase

from microsite_configuration.backends.database import DatabaseMicrositeBackend
from microsite_configuration.backends.base import BaseMicrositeBackend
from microsite_configuration.backends.filebased import SettingsFileMicrositeBackend

log = logging.getLogger(__name__)


class NullBackend(BaseMicrositeBackend):
    """
    A class that does nothing but inherit from the base class
    """
    def set_config_by_domain(self, domain):
        """
        For a given request domain, find a match in our microsite configuration
        and make it available to the complete django request process
        """
        return super(NullBackend, self).set_config_by_domain(domain)

    def get_template_path(self, relative_path, **kwargs):
        """
        Returns a path (string) to a Mako template, which can either be in
        an override or will just return what is passed in which is expected to be a string
        """
        return super(NullBackend, self).get_template_path(relative_path, **kwargs)

    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        return super(NullBackend, self).get_value(val_name, default, **kwargs)

    def get_dict(self, dict_name, default={}, **kwargs):
        """
        Returns a dictionary product of merging the request's microsite and
        the default value.
        This can be used, for example, to return a merged dictonary from the
        settings.FEATURES dict, including values defined at the microsite
        """
        return super(NullBackend, self).get_dict(dict_name, default, **kwargs)

    def is_request_in_microsite(self):
        """
        This will return True/False if the current request is a request within a microsite
        """
        return super(NullBackend, self).is_request_in_microsite()

    def has_override_value(self, val_name):
        """
        Returns True/False whether a Microsite has a definition for the
        specified named value
        """
        return super(NullBackend, self).has_override_value(val_name)

    def enable_microsites(self, log):
        """
        Enable the use of microsites.
        Used during the startup.py script
        """
        return super(NullBackend, self).enable_microsites(log)

    def get_all_config(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        return super(NullBackend, self).get_all_config()

    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        return super(NullBackend, self).clear()


class BaseBackendTests(TestCase):
    """
    Go through and test the base abstract class
    """

    def test_cant_create_instance(self):
        """
        We shouldn't be able to create an instance of the base abstract class
        """

        with self.assertRaises(TypeError):
            BaseMicrositeBackend()

    def test_not_yet_implemented(self):
        """
        Make sure all base methods raise a NotImplementedError exception
        """

        backend = NullBackend()

        with self.assertRaises(NotImplementedError):
            backend.set_config_by_domain(None)

        with self.assertRaises(NotImplementedError):
            backend.get_template_path(None)

        with self.assertRaises(NotImplementedError):
            backend.get_value(None, None)

        with self.assertRaises(NotImplementedError):
            backend.get_dict(None, None)

        with self.assertRaises(NotImplementedError):
            backend.is_request_in_microsite()

        with self.assertRaises(NotImplementedError):
            backend.has_override_value(None)

        with self.assertRaises(NotImplementedError):
            backend.get_all_config()

        with self.assertRaises(NotImplementedError):
            backend.clear()
