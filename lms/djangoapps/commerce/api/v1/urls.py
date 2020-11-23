"""
Commerce URLs
"""


from django.conf import settings
from django.conf.urls import include, url

from . import views

COURSE_URLS = ([
    url(r'^$', views.CourseListView.as_view(), name='list'),
    url(r'^{}/$'.format(settings.COURSE_ID_PATTERN), views.CourseRetrieveUpdateView.as_view(), name='retrieve_update'),
], 'courses')

ORDER_URLS = ([
    url(r'^(?P<number>[-\w]+)/$', views.OrderView.as_view(), name='detail'),
], 'orders')

app_name = 'v1'
urlpatterns = [
    url(r'^courses/', include(COURSE_URLS)),
    url(r'^orders/', include(ORDER_URLS)),
]
