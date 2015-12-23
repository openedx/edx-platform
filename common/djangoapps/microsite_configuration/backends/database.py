"""
Microsite backend that reads the configuration from the database

"""
import json

from mako.template import Template
from util.cache import cache

from microsite_configuration.backends.filebased import SettingsFileMicrositeBackend
from microsite_configuration.backends.base import BaseMicrositeTemplateBackend
from microsite_configuration.models import (
    Microsite,
    MicrositeOrgMapping,
    MicrositeTemplate
)
from microsite_configuration.microsite import get_value as microsite_get_value
from django.dispatch import receiver
from django.db.models.signals import post_save


class DatabaseMicrositeBackend(SettingsFileMicrositeBackend):
    """
    Microsite backend that reads the microsites definitions
    from a table in the database according to the models.py file
    """

    def has_configuration_set(self):
        """
        Returns whether there is any Microsite configuration settings
        """
        if Microsite.objects.all()[:1].exists():
            return True
        else:
            return False

    def set_config_by_domain(self, domain):
        """
        For a given request domain, find a match in our microsite configuration
        and then assign it to the thread local in order to make it available
        to the complete Django request processing
        """

        if not self.has_configuration_set or not domain:
            return

        # look up based on the HTTP request domain name
        # this will need to be a full domain name match,
        # not a 'startswith' match
        microsite = Microsite.get_microsite_for_domain(domain)

        if not microsite:
            # if no match, then try to find a 'default' key in Microsites
            try:
                microsite = Microsite.objects.get(key='default')
            except Microsite.DoesNotExist:
                pass

        if microsite:
            # if we have a match, then set up the microsite thread local
            # data
            self._set_microsite_config_from_obj(microsite.subdomain, domain, microsite)

    def get_all_config(self):
        """
        This returns all configuration for all microsites
        """
        config = {}

        candidates = Microsite.objects.all()
        for microsite in candidates:
            values = microsite.values
            config[microsite.key] = values

        return config

    def get_value_for_org(self, org, val_name, default=None):
        """
        This returns a configuration value for a microsite which has an org_filter that matches
        what is passed in
        """

        microsite = MicrositeOrgMapping.get_microsite_for_org(org)
        if not microsite:
            return default

        # cdodge: This approach will not leverage any caching, although I think only Studio calls
        # this
        config = microsite.values
        return config.get(val_name, default)

    def get_all_orgs(self):
        """
        This returns a set of orgs that are considered within a microsite. This can be used,
        for example, to do filtering
        """

        # This should be cacheable (via memcache to keep consistent across a cluster)
        # I believe this is called on the dashboard and catalog pages, so it'd be good to optimize
        return set(MicrositeOrgMapping.objects.all().values_list('org', flat=True))

    def _set_microsite_config_from_obj(self, subdomain, domain, microsite_object):
        """
        Helper internal method to actually find the microsite configuration
        """
        config = microsite_object.values
        config['subdomain'] = subdomain
        config['site_domain'] = domain
        config['microsite_config_key'] = microsite_object.key

        # we take the list of ORGs associated with this microsite from the database mapping
        # tables. NOTE, for now, we assume one ORG per microsite
        orgs = microsite_object.get_orgs()

        # we must have at least one ORG defined
        if not orgs:
            raise Exception(
                'Configuration error. Microsite {key} does not have any ORGs mapped to it!'.format(
                    key=microsite_object.key
                )
            )

        # just take the first one for now, we'll have to change the upstream logic to allow
        # for more than one ORG binding
        config['course_org_filter'] = orgs[0]
        self.current_request_configuration.data = config


class DatabaseMicrositeTemplateBackend(BaseMicrositeTemplateBackend):
    """
    Specialized class to pull templates from the database
    """
    def get_template_path(self, relative_path, **kwargs):
        return relative_path

    def get_template(self, uri):
        """
        Override of the base class for us to look into the
        database tables for a template definition, if we can't find
        one we'll return None which means "use default means" (aka filesystem)
        """
        cache_key = "template_cache." + microsite_get_value('microsite_config_key') + '.' + uri
        template_text = cache.get(cache_key)  # pylint: disable=maybe-no-member

        if not template_text:
            # Don't use the cache
            template_obj = MicrositeTemplate.get_template_for_microsite(
                microsite_get_value('microsite_config_key'),
                uri
            )

            if not template_obj:
                # We need to set something in the cache to improve performance
                # of the templates stored in the filesystem as well
                cache.set(cache_key, '##none', 60 * 5)  # pylint: disable=maybe-no-member
                return None

            template_text = template_obj.template
            cache.set(cache_key, template_text, 60 * 3)  # pylint: disable=maybe-no-member

        if template_text == '##none':
            return None

        return Template(
            text=template_text
        )

    @staticmethod
    @receiver(post_save, sender=MicrositeTemplate)
    def clear_cache(sender, instance, **kwargs):  # pylint: disable=unused-argument
        """
        Clear the cached template when the model is saved
        """
        cache_key = "template_cache." + instance.microsite.key + '.' + instance.template_uri
        cache.delete(cache_key)  # pylint: disable=maybe-no-member
