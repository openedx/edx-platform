"""
Template tags and helper functions for displaying breadcrumbs in page titles
based on the current micro site.
"""
from django import template
from django.conf import settings
from microsite_configuration import microsite
from django.templatetags.static import static

register = template.Library()


def page_title_breadcrumbs(*crumbs, **kwargs):
    """
    This function creates a suitable page title in the form:
    Specific | Less Specific | General | edX
    It will output the correct platform name for the request.
    Pass in a `separator` kwarg to override the default of " | "
    """
    separator = kwargs.get("separator", " | ")
    if crumbs:
        return u'{}{}{}'.format(separator.join(crumbs), separator, platform_name())
    else:
        return platform_name()


@register.simple_tag(name="page_title_breadcrumbs", takes_context=True)
def page_title_breadcrumbs_tag(context, *crumbs):
    """
    Django template that creates breadcrumbs for page titles:
    {% page_title_breadcrumbs "Specific" "Less Specific" General %}
    """
    return page_title_breadcrumbs(*crumbs)


@register.simple_tag(name="platform_name")
def platform_name():
    """
    Django template tag that outputs the current platform name:
    {% platform_name %}
    """
    return microsite.get_value('platform_name', settings.PLATFORM_NAME)


@register.simple_tag(name="favicon_path")
def favicon_path(default=getattr(settings, 'FAVICON_PATH', 'images/favicon.ico')):
    """
    Django template tag that outputs the configured favicon:
    {% favicon_path %}
    """
    return static(microsite.get_value('favicon_path', default))


@register.simple_tag(name="microsite_css_overrides_file")
def microsite_css_overrides_file():
    """
    Django template tag that outputs the css import for a:
    {% microsite_css_overrides_file %}
    """
    file_path = microsite.get_value('css_overrides_file', None)
    if file_path is not None:
        return "<link href='{}' rel='stylesheet' type='text/css'>".format(static(file_path))
    else:
        return ""
