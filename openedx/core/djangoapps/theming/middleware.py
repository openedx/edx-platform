"""
Middleware for theming app

Note:
    This middleware depends on "django_sites_extensions" app
    So it must be added to INSTALLED_APPS in django settings files.
"""
from django.conf import settings

from .models import SiteTheme
from .views import get_user_preview_site_theme, set_user_preview_site_theme

PREVIEW_THEME_FIELD = 'preview_theme'


class CurrentSiteThemeMiddleware(object):
    """
    Middleware that sets `site_theme` attribute to request object.
    """
    def process_request(self, request):
        """
        Set the request's 'site_theme' attribute based upon the current user.
        """
        # If this is a post, apply any updates first
        if 'set_preview_theme' in request.POST:
            preview_theme_name = request.POST.get(PREVIEW_THEME_FIELD, '')
            set_user_preview_site_theme(request, preview_theme_name)
        elif 'reset_preview_theme' in request.POST:
            set_user_preview_site_theme(request, None)

        # Determine if the user has specified a preview site
        preview_site_theme = get_user_preview_site_theme(request)
        if preview_site_theme:
            site_theme = preview_site_theme
        else:
            default_theme = None
            if settings.DEFAULT_SITE_THEME:
                default_theme = SiteTheme(site=request.site, theme_dir_name=settings.DEFAULT_SITE_THEME)
            site_theme = SiteTheme.get_theme(request.site, default=default_theme)
        request.site_theme = site_theme
