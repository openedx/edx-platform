"""
Views file for the Darklang Django App
"""

from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangoapps.user_api.preferences.api import (
    delete_user_preference,
    get_user_preference,
    set_user_preference,
)
from openedx.core.djangoapps.util.user_messages import (
    register_error_message,
    register_success_message,
)
from web_fragments.fragment import Fragment

from .helpers import theme_exists
from .models import SiteTheme

PREVIEW_SITE_THEME_PREFERENCE_KEY = 'preview-site-theme'


def get_user_preview_site_theme(request):
    """
    Returns the preview site for the current user, or None if not set.
    """
    preview_site_name = get_user_preference(request.user, PREVIEW_SITE_THEME_PREFERENCE_KEY)
    if not preview_site_name:
        return None
    return SiteTheme(site=request.site, theme_dir_name=preview_site_name)


def set_user_preview_site_theme(request, preview_site_theme):
    """
    Sets the current user's preferred preview site theme.

    Args:
        request: the current request
        preview_site_theme: the preview site theme (or None to remove it)
    """
    if preview_site_theme:
        if isinstance(preview_site_theme, SiteTheme):
            preview_site_theme_name = preview_site_theme.theme_dir_name
        else:
            preview_site_theme_name = preview_site_theme
        if theme_exists(preview_site_theme_name):
            set_user_preference(request.user, PREVIEW_SITE_THEME_PREFERENCE_KEY, preview_site_theme_name)
            register_success_message(
                request,
                _('Site theme changed to {site_theme}'.format(site_theme=preview_site_theme_name))
            )
        else:
            register_error_message(
                request,
                _('Theme {site_theme} does not exist'.format(site_theme=preview_site_theme_name))
            )
    else:
        delete_user_preference(request.user, PREVIEW_SITE_THEME_PREFERENCE_KEY)
        register_success_message(request, _('Site theme reverted to the default'))


class ThemingAdministrationFragmentView(EdxFragmentView):
    """
    Fragment view to allow a user to administer theming.
    """

    def render_to_fragment(self, request, course_id=None, **kwargs):
        """
        Renders the theming administration view as a fragment.
        """
        context = {
            'preview_site_theme': get_user_preview_site_theme(request),
        }
        html = render_to_string('theming/theming-admin-fragment.html', context)
        fragment = Fragment(html)
        self.add_fragment_resource_urls(fragment)
        return fragment

    def post(self, request, *args, **kwargs):
        """
        Accept a post request, and then render the fragment to HTML.

        Note: the middleware will handle updates to the preview theme.
        """
        return self.get(request, *args, **kwargs)

    def create_base_standalone_context(self, request, fragment, **kwargs):
        """
        Creates the context to use when rendering a standalone page.
        """
        return {
            'uses_bootstrap': True,
        }

    def standalone_page_title(self, request, fragment, **kwargs):
        """
        Returns the page title for the standalone update page.
        """
        return _('Theming Administration')
