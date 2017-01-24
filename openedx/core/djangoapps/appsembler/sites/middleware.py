from django.conf import settings
from django.core.cache import cache
from django.contrib.redirects.models import Redirect
from django.shortcuts import redirect


class RedirectMiddleware(object):
    """
    Redirects requests for URLs persisted using the django.contrib.redirects.models.Redirect model.
    With the exception of the main site.
    """
    def process_request(self, request):
        """
        Redirects the current request if there is a matching Redirect model
        with the current request URL as the old_path field.
        """
        site = request.site
        try:
            in_whitelist = any(map(
                lambda p: p in request.path,
                settings.MAIN_SITE_REDIRECT_WHITELIST))
            if (site.id == settings.SITE_ID) and not in_whitelist:
                return redirect(settings.AMC_APP_URL)
        except Exception:
            # I'm not entirely sure this middleware get's called only in LMS or in other apps as well.
            # Soooo just in case
            pass
        cache_key = '{prefix}-{site}'.format(prefix=settings.REDIRECT_CACHE_KEY_PREFIX, site=site.domain)
        redirects = cache.get(cache_key)
        if redirects is None:
            redirects = {redirect.old_path: redirect.new_path for redirect in Redirect.objects.filter(site=site)}
            cache.set(cache_key, redirects, settings.REDIRECT_CACHE_TIMEOUT)
        redirect_to = redirects.get(request.path)
        if redirect_to:
            return redirect(redirect_to, permanent=True)

