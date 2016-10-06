"""
URLs for static_template_view app
"""

from django.conf import settings
from django.conf.urls import patterns, url

urlpatterns = (
    'static_template_view.views',

    # TODO: Is this used anymore? What is STATIC_GRAB?
    url(r'^t/(?P<template>[^/]*)$', 'index'),

    # Semi-static views (these need to be rendered and have the login bar, but don't change)
    url(r'^404$', 'render', {'template': '404.html'}, name="404"),
    # display error page templates, for testing purposes
    url(r'^404$', 'render_404'),  # Can this be deleted? Test test_404_microsites fails with this.
    url(r'^500$', 'render_500'),

    url(r'^blog$', 'render', {'template': 'blog.html'}, name="blog"),
    url(r'^contact$', 'render', {'template': 'contact.html'}, name="contact"),
    url(r'^donate$', 'render', {'template': 'donate.html'}, name="donate"),
    url(r'^faq$', 'render', {'template': 'faq.html'}, name="faq"),
    url(r'^help$', 'render', {'template': 'help.html'}, name="help_edx"),
    url(r'^jobs$', 'render', {'template': 'jobs.html'}, name="jobs"),
    url(r'^news$', 'render', {'template': 'news.html'}, name="news"),
    url(r'^press$', 'render', {'template': 'press.html'}, name="press"),
    url(r'^media-kit$', 'render', {'template': 'media-kit.html'}, name="media-kit"),
    url(r'^copyright$', 'render', {'template': 'copyright.html'}, name="copyright"),

    # Press releases
    url(r'^press/([_a-zA-Z0-9-]+)$', 'render_press_release', name='press_release'),
)

# Only enable URLs for those marketing links actually enabled in the
# settings. Disable URLs by marking them as None.
for key, value in settings.MKTG_URL_LINK_MAP.items():
    # Skip disabled URLs
    if value is None:
        continue

    # These urls are enabled separately
    if key == "ROOT" or key == "COURSES":
        continue

    # The MKTG_URL_LINK_MAP key specifies the template filename
    template = key.lower()
    if '.' not in template:
        # Append STATIC_TEMPLATE_VIEW_DEFAULT_FILE_EXTENSION if
        # no file extension was specified in the key
        template = "%s.%s" % (template, settings.STATIC_TEMPLATE_VIEW_DEFAULT_FILE_EXTENSION)

    # Make the assumption that the URL we want is the lowercased
    # version of the map key
    urlpatterns += (url(r'^%s$' % key.lower(), 'render', {'template': template}, name=value),)

urlpatterns = patterns(*urlpatterns)
