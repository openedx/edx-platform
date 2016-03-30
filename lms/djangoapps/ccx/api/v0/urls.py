""" CCX API v0 URLs. """

from django.conf import settings
from django.conf.urls import patterns, url, include

from lms.djangoapps.ccx.api.v0 import views

CCX_COURSE_ID_PATTERN = settings.COURSE_ID_PATTERN.replace('course_id', 'ccx_course_id')

CCX_URLS = patterns(
    '',
    url(r'^$', views.CCXListView.as_view(), name='list'),
    url(r'^{}/?$'.format(CCX_COURSE_ID_PATTERN), views.CCXDetailView.as_view(), name='detail'),
)

urlpatterns = patterns(
    '',
    url(r'^ccx/', include(CCX_URLS, namespace='ccx')),
)
