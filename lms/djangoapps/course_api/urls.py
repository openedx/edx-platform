"""
Course API URLs
"""


from django.conf import settings
from django.conf.urls import include, url

from .views import CourseDetailView, CourseIdListView, CourseListView

urlpatterns = [
    url(r'^v1/courses/$', CourseListView.as_view(), name="course-list"),
    url(r'^v1/courses/{}'.format(settings.COURSE_KEY_PATTERN), CourseDetailView.as_view(), name="course-detail"),
    url(r'^v1/course_ids/$', CourseIdListView.as_view(), name="course-id-list"),
    url(r'', include('lms.djangoapps.course_api.blocks.urls'))
]
