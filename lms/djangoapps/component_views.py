"""
Support for LMS component views.
"""

from django.conf import settings
from django.shortcuts import render_to_response
from django.templatetags.static import static
from django.utils.translation import get_language_bidi

from django_component_views.component_views import ComponentView


class LmsComponentView(ComponentView):
    """
    The base class of all edx-platform component views.
    """
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

    def add_resource_urls(self, fragment):
        """
        Adds URLs for JS and CSS resources that this XBlock depends on to `fragment`.
        """
        # Head dependencies
        for vendor_js_file in self.vendor_js_dependencies():
            fragment.add_resource_url(static(vendor_js_file), "application/javascript", "head")

        for css_file in self.css_dependencies():
            fragment.add_css_url(static(css_file))

        # Body dependencies
        for js_file in self.js_dependencies():
            fragment.add_javascript_url(static(js_file))

    def vendor_js_dependencies(self):
        """
        Returns the vendor dependencies for this component.
        """
        return []

    def js_dependencies(self):
        """
        Returns the JavaScript dependencies for this component.
        """
        return []

    def css_dependencies(self):
        """
        Returns the CSS dependencies for this component.
        """
        if get_language_bidi():
            return self.get_css_dependencies('style-main-v2-rtl')
        else:
            return self.get_css_dependencies('style-main-v2')

    def render_standalone_html(self, fragment):
        """
        """
        context = {
            'settings': settings,
            'fragment': fragment,
            'uses-pattern-library': True,
        }
        return render_to_response('component-chromeless.html', context)
