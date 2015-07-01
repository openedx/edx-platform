""" API v1 URLs. """
from django.conf import settings
from django.conf.urls import patterns, url, include

from commerce.api.v1 import views

COURSE_URLS = patterns(
    '',
    url(r'^$', views.CourseListView.as_view(), name='list'),
    url(r'^{}/$'.format(settings.COURSE_ID_PATTERN), views.CourseRetrieveUpdateView.as_view(), name='retrieve_update'),
)

urlpatterns = patterns(
    '',
    url(r'^courses/', include(COURSE_URLS, namespace='courses')),

)
