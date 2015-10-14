"""
Microsite configuration backend module.

Contains the base class for microsite backends.

"""

from __future__ import absolute_import

import abc
import edxmako
import os.path

from django.conf import settings


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
        raise NotImplementedError()

    def get_template_path(self, relative_path, **kwargs):
        """
        Returns a path (string) to a Mako template, which can either be in
        an override or will just return what is passed in which is expected to be a string
        """
        if not self.is_request_in_microsite():
            return relative_path

        microsite_template_path = str(self.get_value('template_dir', None))

        if microsite_template_path:
            search_path = os.path.join(microsite_template_path, relative_path)

            if os.path.isfile(search_path):
                path = '/{0}/templates/{1}'.format(
                    self.get_value('microsite_config_key'),
                    relative_path
                )
                return path

        return relative_path

    @abc.abstractmethod
    def get_value(self, val_name, default=None, **kwargs):
        """
        Returns a value associated with the request's microsite, if present
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_dict(self, dict_name, default={}, **kwargs):
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

    def enable_microsites(self, log):
        """
        Enable the use of microsites, from a dynamic defined list in the db
        """
        if not settings.FEATURES['USE_MICROSITES']:
            return

        microsites_root = settings.MICROSITE_ROOT_DIR

        if os.path.isdir(microsites_root):
            settings.TEMPLATE_DIRS.append(microsites_root)
            edxmako.paths.add_lookup('main', microsites_root)
            settings.STATICFILES_DIRS.insert(0, microsites_root)

            log.info('Loading microsite path at %s', microsites_root)
        else:
            log.error(
                'Error loading %s. Directory does not exist',
                microsites_root
            )

    @abc.abstractmethod
    def get_all_config(self):
        """
        This returns a set of orgs that are considered within all microsites.
        This can be used, for example, to do filtering
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def clear(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        raise NotImplementedError()
