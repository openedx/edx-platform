""" Django Sites framework models overrides """
from django.conf import settings
from django.core.cache import caches
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.http.request import split_domain_port
from django.contrib.sites.models import Site, SiteManager, SITE_CACHE
from django.core.exceptions import ImproperlyConfigured
import django

cache = caches['general']


def _cache_key_for_site_id(site_id):
    return 'site:id:%s' % (site_id,)


def _cache_key_for_site_host(site_host):
    return 'site:host:%s' % (site_host,)


def patched_get_site_by_id(self, site_id):
    key = _cache_key_for_site_id(site_id)
    site = cache.get(key)
    if site is None:
        site = self.get(pk=site_id)
        SITE_CACHE[site_id] = site
    cache.add(key, site)
    return site


def patched_get_site_by_request(self, request):

    host = request.get_host()
    key = _cache_key_for_site_host(host)
    site = cache.get(key)
    if site is None:
        try:
            # First attempt to look up the site by host with or without port.
            site = self.get(domain__iexact=host)
        except Site.DoesNotExist:
            # Fallback to looking up site after stripping port from the host.
            domain, port = split_domain_port(host)
            if not port:
                raise
            site = self.get(domain__iexact=domain)
        SITE_CACHE[host] = site
    cache.add(key, site)
    return site


def patched_clear_cache(self):
    keys_id = [_cache_key_for_site_id(site_id) for site_id in SITE_CACHE]
    keys_host = [_cache_key_for_site_host(site_host) for site_host in SITE_CACHE]
    cache.delete_many(keys_id + keys_host)
    SITE_CACHE.clear()


def patched_clear_site_cache(sender, **kwargs):
    """
    Clears the cache (if primed) each time a site is saved or deleted
    """
    instance = kwargs['instance']
    site = instance.site
    key_id = _cache_key_for_site_id(site.pk)
    key_host = _cache_key_for_site_host(site.domain)
    cache.delete_many([key_id, key_host])
    try:
        del SITE_CACHE[site.pk]
    except KeyError:
        pass
    try:
        del SITE_CACHE[site.domain]
    except KeyError:
        pass


class AlternativeDomain(models.Model):
    site = models.OneToOneField(Site, related_name='alternative_domain')
    domain = models.CharField(max_length=500)
    app_label = "appsembler"
    
    def __unicode__(self):
        return self.domain

    def switch_with_active(self):
        """
        Switches the currently active site with the alternative domain (custom or default) and saves
        the currently active site as the alternative domain.
        """
        current_domain = self.site.domain
        self.site.domain = self.domain
        self.domain = current_domain
        self.site.save()
        self.save()

    def is_tahoe_domain(self):
        """
        Checks if the domain is the default Tahoe domain and not a custom domain
        :return:
        """
        return settings.LMS_BASE in self.domain


@receiver(post_save, sender=AlternativeDomain)
def delete_alternative_domain_cache(sender, instance, **kwargs):
    if instance.site.domain.endswith(settings.SITE_NAME):
        cache_key_site = instance.site.domain
    else:
        cache_key_site = instance.domain

    cache_key = '{prefix}-{site}'.format(
        prefix=settings.CUSTOM_DOMAINS_REDIRECT_CACHE_KEY_PREFIX,
        site=cache_key_site
    )
    cache.delete(cache_key)

django.contrib.sites.models.clear_site_cache = patched_clear_site_cache
SiteManager.clear_cache = patched_clear_cache
SiteManager._get_site_by_id = patched_get_site_by_id  # pylint: disable=protected-access
SiteManager._get_site_by_request = patched_get_site_by_request  # pylint: disable=protected-access
