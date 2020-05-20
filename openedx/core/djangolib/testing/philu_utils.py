"""Utility methods and classes for testing django applications."""

from django.contrib.sites.models import Site

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.theming.models import SiteTheme


def intercept_renderer(path, context):
    """
    Intercept calls to `render_to_response` and attach the context dict to the
    response for examination in unit tests.
    """
    response = render_to_response(path, context)
    response.mako_context = context
    response.mako_template = path
    return response


def configure_philu_theme():
    site = Site(domain='testserver', name='test')
    site.save()
    theme = SiteTheme(site=site, theme_dir_name='philu')
    theme.save()


def clear_philu_theme():
    Site.objects.filter(name='test').delete()
    SiteTheme.objects.filter(theme_dir_name='philu').delete()
