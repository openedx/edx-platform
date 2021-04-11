"""
URLs for static_template_view app
"""


from django.conf import settings
from django.conf.urls import url

from lms.djangoapps.static_template_view import views

urlpatterns = [
    # Semi-static views (these need to be rendered and have the login bar, but don't change)
    url(r'^404$', views.render, {'template': '404.html'}, name="404"),
    # display error page templates, for testing purposes
    url(r'^404$', views.render_404, name='static_template_view.views.render_404'),
    url(r'^500$', views.render_500, name='static_template_view.views.render_500'),

    url(r'^blog$', views.render, {'template': 'blog.html'}, name="blog"),
    url(r'^contact$', views.render, {'template': 'contact.html'}, name="contact"),
    url(r'^donate$', views.render, {'template': 'donate.html'}, name="donate"),
    url(r'^faq$', views.render, {'template': 'faq.html'}, name="faq"),
    url(r'^help$', views.render, {'template': 'help.html'}, name="help_edx"),
    url(r'^jobs$', views.render, {'template': 'jobs.html'}, name="jobs"),
    url(r'^news$', views.render, {'template': 'news.html'}, name="news"),
    url(r'^press$', views.render, {'template': 'press.html'}, name="press"),
    url(r'^media-kit$', views.render, {'template': 'media-kit.html'}, name="media-kit"),
    url(r'^copyright$', views.render, {'template': 'copyright.html'}, name="copyright"),

    # Press releases
    url(r'^press/([_a-zA-Z0-9-]+)$', views.render_press_release, name='press_release'),
]

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
    urlpatterns.append(url(r'^%s$' % key.lower(), views.render, {'template': template}, name=value))
