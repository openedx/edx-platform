import beeline
import logging

from django.conf import settings
from django.core.cache import caches
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

from openedx.core.djangoapps.appsembler.sites.models import AlternativeDomain
from openedx.core.djangoapps.appsembler.sites.utils import get_current_organization


log = logging.getLogger(__name__)


class CustomDomainsRedirectMiddleware(MiddlewareMixin):

    def process_request(self, request):
        cache_general = caches['default']
        hostname = request.get_host()
        if hostname.endswith(settings.SITE_NAME):
            cache_key = '{prefix}-{site}'.format(prefix=settings.CUSTOM_DOMAINS_REDIRECT_CACHE_KEY_PREFIX, site=hostname)
            custom_domain = cache_general.get(cache_key)
            if custom_domain is None:
                beeline.add_trace_field("custom_domain_cache_hit", False)
                try:
                    alternative_domain = AlternativeDomain.objects.select_related('site').get(domain=hostname)
                    custom_domain = alternative_domain.site.domain
                except AlternativeDomain.DoesNotExist:
                    custom_domain = ""
                cache_general.set(cache_key, custom_domain, settings.CUSTOM_DOMAINS_REDIRECT_CACHE_TIMEOUT)
            else:
                beeline.add_trace_field("custom_domain_cache_hit", True)

            if custom_domain:
                return redirect("https://" + custom_domain)

            return


class RedirectMiddleware(MiddlewareMixin):
    """
    Redirects requests for main site to Tahoe marketing page, except whitelisted.
    """
    def process_request(self, request):
        """
        Redirects the current request if there is a matching Redirect model
        with the current request URL as the old_path field.
        """
        site = request.site
        try:
            beeline.add_trace_field("site_id", site.id)
            in_whitelist = any([p in request.path for p in settings.MAIN_SITE_REDIRECT_ALLOWLIST])
            if (site.id == settings.SITE_ID) and not in_whitelist:
                return redirect(settings.TAHOE_MAIN_SITE_REDIRECT_URL)
        except Exception:
            # I'm not entirely sure this middleware get's called only in LMS or in other apps as well.
            # Soooo just in case
            beeline.add_trace_field("redirect_middleware_exception", True)
            pass


class LmsCurrentOrganizationMiddleware(RedirectMiddleware):
    """
    Get the current middleware for the LMS.

    This middleware replaces the default `organizations.OrganizationMiddleware` to
    use a better get_current_organization() helper.
    """
    def process_request(self, request):
        # Note: This does _not_ support multiple organizations per user.
        organization = get_current_organization(failure_return_none=True)
        beeline.add_trace_field('session_current_organization', organization)
        request.session['organization'] = organization
