"""
Middleware for theming app

Note:
    This middleware depends on "django_sites_extensions" app
    So it must be added to INSTALLED_APPS in django settings files.
"""


from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from .models import SiteTheme
from .views import get_user_preview_site_theme


class CurrentSiteThemeMiddleware(MiddlewareMixin):
    """
    Middleware that sets `site_theme` attribute to request object.
    """
    def process_request(self, request):
        """
        Set the request's 'site_theme' attribute based upon the current user.
        """
        # Specifying a "site_theme" querystring param takes precedence
        qs_theme = request.GET.get('site_theme')

        # Determine if the user has specified a preview site
        preview_site_theme = get_user_preview_site_theme(request)

        if qs_theme:
            site_theme = SiteTheme(site=request.site, theme_dir_name=qs_theme)
        elif preview_site_theme:
            site_theme = preview_site_theme
        else:
            default_theme = None
            if settings.DEFAULT_SITE_THEME:
                default_theme = SiteTheme(site=request.site, theme_dir_name=settings.DEFAULT_SITE_THEME)
            site_theme = SiteTheme.get_theme(request.site, default=default_theme)
        request.site_theme = site_theme
