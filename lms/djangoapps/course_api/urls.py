"""
Course API URLs
"""


from django.conf import settings
from django.conf.urls import include, url

from .views import CourseDetailView, CourseDetailViewV2, CourseListView

urlpatterns = [
    url(r'^v1/courses/$', CourseListView.as_view(), name="course-list"),
    url(r'^v1/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseDetailView.as_view(), name="course-detail"),
    url(r'^v2/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseDetailViewV2.as_view(), name="course-detail-v2"),
    url(r'', include('course_api.blocks.urls'))
]
