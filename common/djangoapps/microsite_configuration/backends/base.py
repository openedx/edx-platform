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

    def enable_microsites(self, log):
        """
        Enable the use of microsites, from a dynamic defined list in the db
        """
        if not settings.FEATURES['USE_MICROSITES']:
            return

        microsites_root = settings.MICROSITE_ROOT_DIR

        if os.path.isdir(microsites_root):
            settings.DEFAULT_TEMPLATE_ENGINE['DIRS'].insert(0, microsites_root)
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


class BaseMicrositeTemplateBackend(object):
    """
    Interface for microsite template providers. Base implementation is to use the filesystem
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
