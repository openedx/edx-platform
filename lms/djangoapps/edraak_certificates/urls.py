from django.conf import settings
from django.conf.urls import patterns, url
from django.core.urlresolvers import LocaleRegexURLResolver

urlpatterns = patterns('',  # nopep8
                       url(r'^issue$', 'edraak_certificates.views.issue', name='edraak_certificates_issue'),

                       url(r'^download/(?P<course_id>[^/]+/[^/]+/[^/]+)$', 'edraak_certificates.views.download',
                           name='edraak_certificates_download'),

                       url(r'^preview/(?P<course_id>[^/]+/[^/]+/[^/]+)$', 'edraak_certificates.views.preview',
                           name='edraak_certificates_preview'),
)
