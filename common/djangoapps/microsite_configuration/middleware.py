"""
This file implements the initial Microsite support for the Open edX platform.
A microsite enables the following features:

1) Mapping of sub-domain name to a 'brand', e.g. foo-university.edx.org
2) Present a landing page with a listing of courses that are specific to the 'brand'
3) Ability to swap out some branding elements in the website
"""
import threading
import os.path

from django.conf import settings

_microsite_configuration_threadlocal = threading.local()
_microsite_configuration_threadlocal.data = {}


def has_microsite_configuration_set():
    """
    Returns whether the MICROSITE_CONFIGURATION has been set in the configuration files
    """
    return getattr(settings, "MICROSITE_CONFIGURATION", False)


class MicrositeConfiguration(object):
    """
    Middleware class which will bind configuration information regarding 'microsites' on a per request basis.
    The actual configuration information is taken from Django settings information
    """

    @classmethod
    def is_request_in_microsite(cls):
        """
        This will return if current request is a request within a microsite
        """
        return cls.get_microsite_configuration()

    @classmethod
    def get_microsite_configuration(cls):
        """
        Returns the current request's microsite configuration
        """
        if not hasattr(_microsite_configuration_threadlocal, 'data'):
            return {}

        return _microsite_configuration_threadlocal.data

    @classmethod
    def get_microsite_configuration_value(cls, val_name, default=None):
        """
        Returns a value associated with the request's microsite, if present
        """
        configuration = cls.get_microsite_configuration()
        return configuration.get(val_name, default)

    @classmethod
    def get_microsite_template_path(cls, relative_path):
        """
        Returns a path to a Mako template, which can either be in
        a microsite directory (as an override) or will just return what is passed in
        """

        if not cls.is_request_in_microsite():
            return relative_path

        microsite_template_path = cls.get_microsite_configuration_value('template_dir')

        if microsite_template_path:
            search_path = microsite_template_path / relative_path

            if os.path.isfile(search_path):
                path = '{0}/templates/{1}'.format(
                    cls.get_microsite_configuration_value('microsite_name'),
                    relative_path
                )
                return path

        return relative_path

    @classmethod
    def get_microsite_configuration_value_for_org(cls, org, val_name, default=None):
        """
        This returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """
        if not has_microsite_configuration_set():
            return default

        for key in settings.MICROSITE_CONFIGURATION.keys():
            org_filter = settings.MICROSITE_CONFIGURATION[key].get('course_org_filter', None)
            if org_filter == org:
                return settings.MICROSITE_CONFIGURATION[key].get(val_name, default)
        return default

    @classmethod
    def get_all_microsite_orgs(cls):
        """
        This returns a set of orgs that are considered within a Microsite. This can be used,
        for example, to do filtering
        """
        org_filter_set = []
        if not has_microsite_configuration_set():
            return org_filter_set

        for key in settings.MICROSITE_CONFIGURATION:
            org_filter = settings.MICROSITE_CONFIGURATION[key].get('course_org_filter')
            if org_filter:
                org_filter_set.append(org_filter)

        return org_filter_set

    def clear_microsite_configuration(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        _microsite_configuration_threadlocal.data = {}

    def process_request(self, request):
        """
        Middleware entry point on every request processing. This will associate a request's domain name
        with a 'University' and any corresponding microsite configuration information
        """
        self.clear_microsite_configuration()

        domain = request.META.get('HTTP_HOST', None)

        if domain:
            subdomain = MicrositeConfiguration.pick_subdomain(domain, settings.SUBDOMAIN_BRANDING.keys())
            university = MicrositeConfiguration.match_university(subdomain)
            microsite_configuration = self.get_microsite_configuration_for_university(university)
            if microsite_configuration:
                microsite_configuration['university'] = university
                microsite_configuration['subdomain'] = subdomain
                microsite_configuration['site_domain'] = domain
                _microsite_configuration_threadlocal.data = microsite_configuration

        # also put the configuration on the request itself to make it easier to dereference
        request.microsite_configuration = _microsite_configuration_threadlocal.data
        return None

    def process_response(self, request, response):
        """
        Middleware entry point for request completion.
        """
        self.clear_microsite_configuration()
        return response

    def get_microsite_configuration_for_university(self, university):
        """
        For a given university, return the microsite configuration which
        is in the Django settings
        """
        if not university:
            return None

        if not has_microsite_configuration_set():
            return None

        configuration = settings.MICROSITE_CONFIGURATION.get(university, None)
        return configuration

    @classmethod
    def match_university(cls, domain):
        """
        Return the university name specified for the domain, or None
        if no university was specified
        """
        if not settings.FEATURES['SUBDOMAIN_BRANDING'] or domain is None:
            return None

        subdomain = cls.pick_subdomain(domain, settings.SUBDOMAIN_BRANDING.keys())
        return settings.SUBDOMAIN_BRANDING.get(subdomain)

    @classmethod
    def pick_subdomain(cls, domain, options, default='default'):
        """
        Attempt to match the incoming request's HOST domain with a configuration map
        to see what subdomains are supported in Microsites.
        """
        for option in options:
            if domain.startswith(option):
                return option
        return default
