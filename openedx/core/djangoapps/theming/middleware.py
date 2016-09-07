"""
Middleware for theming app

Note:
    This middleware depends on "django_sites_extensions" app
    So it must be added to INSTALLED_APPS in django settings files.
"""
from django.conf import settings
from openedx.core.djangoapps.theming.models import SiteTheme


class CurrentSiteThemeMiddleware(object):
    """
    Middleware that sets `site_theme` attribute to request object.
    """

    def process_request(self, request):
        """
        fetch Site Theme for the current site and add it to the request object.
        """
        default_theme = SiteTheme(site=request.site, theme_dir_name=settings.DEFAULT_SITE_THEME)
        request.site_theme = SiteTheme.get_theme(request.site, default=default_theme)
