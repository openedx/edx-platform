"""
This file implements the initial Microsite support for the Open edX platform.
A microsite enables the following features:

1) Mapping of sub-domain name to a 'brand', e.g. foo-university.edx.org
2) Present a landing page with a listing of courses that are specific to the 'brand'
3) Ability to swap out some branding elements in the website
"""
import threading

from django.conf import settings

from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO

_microsite_configuration_threadlocal = threading.local()
_microsite_configuration_threadlocal.data = {}

def has_microsite_configuration_set():
    """
    Returns whether the MICROSITE_CONFIGURATION has been set in the configuration files
    """
    return hasattr(settings, "MICROSITE_CONFIGURATION") and settings.MICROSITE_CONFIGURATION


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
        return cls.get_microsite_configuration() != None

    @classmethod
    def has_microsite_email_template_definition(cls, template_name):
        """
        """
        return cls.is_request_in_microsite() and cls.get_microsite_email_template_definitions(
            template_name) != None

    @classmethod
    def get_microsite_configuration(cls):
        """
        Returns the current request's microsite configuration
        """
        return _microsite_configuration_threadlocal.data

    @classmethod
    def get_microsite_configuration_value(cls, val_name, default=None):
        """
        Returns a value associated with the request's microsite, if present
        """
        configuration = cls.get_microsite_configuration()
        return configuration.get(val_name, default)

    @classmethod
    def get_microsite_email_template_definitions(cls, template_name):
        """
        Returns the template definitions associated with a Microsite
        """
        configuration = cls.get_microsite_configuration()
        if configuration and 'email_templates' in configuration:
            return configuration['email_templates'].get(template_name, None)

        return None        

    @classmethod
    def render_microsite_email_template(cls, template_name, params):
        """
        Returns a string pair which is a rendered version of an email template of a given name
        """
        subject = None
        message = None

        email_template_definitions = cls.get_microsite_email_template_definitions(template_name)

        if email_template_definitions:
            # inject a few additional parameters that should be available to all
            # email templates
            p = params.copy()
            p['site_domain'] = cls.get_microsite_configuration_value('site_domain')   
            p['platform_name'] = cls.get_microsite_configuration_value('platform_name')

            buf = StringIO()
            ctx = Context(buf, **p)

            subject_template = Template(email_template_definitions.get('subject', None))
            if subject_template:
                subject_template.render_context(ctx)
                subject = buf.getvalue()

            buf.truncate(0)
            message_template = Template(email_template_definitions.get('body', None))
            if message_template:
                message_template.render_context(ctx)
                message = buf.getvalue()

        return subject, message

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

    def clear_microsite_configuration(self):
        """
        Clears out any microsite configuration from the current request/thread
        """
        _microsite_configuration_threadlocal.data = {}

    def process_request(self, request):
        """
        Middleware entry point on every request processing. This will associate a request's domain name
        with a 'Univserity' and any corresponding microsite configuration information
        """
        self.clear_microsite_configuration()

        domain = request.META.get('HTTP_HOST', None)

        if settings.FEATURES['SUBDOMAIN_BRANDING'] and domain:
            subdomain = self.pick_subdomain(domain, settings.SUBDOMAIN_BRANDING.keys())
            university = self.match_university(subdomain)
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

    def match_university(self, domain):
        """
        Return the university name specified for the domain, or None
        if no university was specified
        """
        if not settings.FEATURES['SUBDOMAIN_BRANDING'] or domain is None:
            return None

        subdomain = self.pick_subdomain(domain, settings.SUBDOMAIN_BRANDING.keys())
        return settings.SUBDOMAIN_BRANDING.get(subdomain)

    def pick_subdomain(self, domain, options, default='default'):
        """
        Attempt to match the incoming request's HOST domain with a configuration map
        to see what subdomains are supported in Microsites.
        """
        for option in options:
            if domain.startswith(option):
                return option
        return default
