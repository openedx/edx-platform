""" Grades API v1 URLs. """
from django.conf import settings
from django.conf.urls import url

from lms.djangoapps.grades.api.v1 import views
from lms.djangoapps.grades.api.views import CourseGradingPolicy

urlpatterns = [
    url(
        r'^courses/$',
        views.CourseGradesView.as_view(), name='course_grades'
    ),
    url(
        r'^courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        views.CourseGradesView.as_view(), name='course_grades'
    ),
    url(
        r'^policy/courses/{course_id}/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        CourseGradingPolicy.as_view(), name='course_grading_policy'
    ),
]
