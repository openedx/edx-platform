""" Django Sites framework models overrides """

from django.core.cache import cache
from django.http.request import split_domain_port
from django.contrib.sites.models import Site, SiteManager, SITE_CACHE
from django.core.exceptions import ImproperlyConfigured
import django


def _cache_key_for_site_id(site_id):
    return 'site:id:%s' % (site_id,)


def _cache_key_for_site_host(site_host):
    return 'site:host:%s' % (site_host,)


def patched_get_current(self, request=None):
    from django.conf import settings
    if getattr(settings, 'SITE_ID', ''):
        site_id = settings.SITE_ID
        return self._get_site_by_id(site_id)
    elif request:
        return self._get_site_by_request(request)

    raise ImproperlyConfigured(
        "You're using the Django \"sites framework\" without having "
        "set the SITE_ID setting. Create a site in your database and "
        "set the SITE_ID setting or pass a request to "
        "Site.objects.get_current() to fix this error."
    )


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
    key_id = _cache_key_for_site_id(instance.pk)
    key_host = _cache_key_for_site_host(instance.domain)
    cache.delete_many([key_id, key_host])
    try:
        del SITE_CACHE[instance.pk]
    except KeyError:
        pass
    try:
        del SITE_CACHE[instance.domain]
    except KeyError:
        pass


django.contrib.sites.models.clear_site_cache = patched_clear_site_cache
SiteManager.get_current = patched_get_current
SiteManager.clear_cache = patched_clear_cache
SiteManager._get_site_by_id = patched_get_site_by_id  # pylint: disable=protected-access
SiteManager._get_site_by_request = patched_get_site_by_request  # pylint: disable=protected-access

