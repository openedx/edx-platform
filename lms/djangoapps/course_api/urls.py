"""
Course API URLs
"""
from django.conf import settings
from django.conf.urls import include, url

from .views import CourseDetailView, CourseListView, CoursePageShareWeixinGetSign

urlpatterns = [
    url(r'^v1/courses/$', CourseListView.as_view(), name="course-list"),
    url(r'^v1/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseDetailView.as_view(), name="course-detail"),
    url(r'^v1/getweixinsign$', CoursePageShareWeixinGetSign.as_view(), name="getweixinsign"),
    url(r'', include('course_api.blocks.urls'))
]
