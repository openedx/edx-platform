"""
Views for building plugins.
"""

from abc import abstractmethod
import logging

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.shortcuts import render_to_response
from web_fragments.views import FragmentView

log = logging.getLogger('plugin_api')


class EdxFragmentView(FragmentView):
    """
    The base class of all Open edX fragment views.
    """
    USES_PATTERN_LIBRARY = True

    page_title = None

    @staticmethod
    def get_css_dependencies(group):
        """
        Returns list of CSS dependencies belonging to `group` in settings.PIPELINE_JS.

        Respects `PIPELINE_ENABLED` setting.
        """
        if settings.PIPELINE_ENABLED:
            return [settings.PIPELINE_CSS[group]['output_filename']]
        else:
            return settings.PIPELINE_CSS[group]['source_filenames']

    @staticmethod
    def get_js_dependencies(group):
        """
        Returns list of JS dependencies belonging to `group` in settings.PIPELINE_JS.

        Respects `PIPELINE_ENABLED` setting.
        """
        if settings.PIPELINE_ENABLED:
            return [settings.PIPELINE_JS[group]['output_filename']]
        else:
            return settings.PIPELINE_JS[group]['source_filenames']

    def vendor_js_dependencies(self):
        """
        Returns list of the vendor JS files that this view depends on.
        """
        return []

    def js_dependencies(self):
        """
        Returns list of the JavaScript files that this view depends on.
        """
        return []

    def css_dependencies(self):
        """
        Returns list of the CSS files that this view depends on.
        """
        return []

    def add_fragment_resource_urls(self, fragment):
        """
        Adds URLs for JS and CSS resources needed by this fragment.
        """
        # Head dependencies
        for vendor_js_file in self.vendor_js_dependencies():
            fragment.add_resource_url(staticfiles_storage.url(vendor_js_file), 'application/javascript', 'head')

        for css_file in self.css_dependencies():
            fragment.add_css_url(staticfiles_storage.url(css_file))

        # Body dependencies
        for js_file in self.js_dependencies():
            fragment.add_javascript_url(staticfiles_storage.url(js_file))

    def render_to_standalone_html(self, request, fragment, **kwargs):
        """
        Renders this fragment to HTML for a standalone page.
        """
        context = {
            'uses-pattern-library': self.USES_PATTERN_LIBRARY,
            'settings': settings,
            'fragment': fragment,
            'disable_accordion': True,
            'allow_iframing': True,
            'disable_header': True,
            'disable_footer': True,
            'disable_window_wrap': True,
            'disable_preview_menu': True,
        }
        return render_to_response(settings.STANDALONE_FRAGMENT_VIEW_TEMPLATE, context)
