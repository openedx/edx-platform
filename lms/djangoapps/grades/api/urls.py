""" Grades API URLs. """
from django.conf import settings
from django.conf.urls import (
    patterns,
    url,
)

from lms.djangoapps.grades.api import views

urlpatterns = patterns(
    '',
    url(
        r'^v0/course_grade/{course_id}/users/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        views.UserGradeView.as_view(), name='user_grade_detail'
    ),
    url(
        r'^v0/courses/{course_id}/policy/$'.format(
            course_id=settings.COURSE_ID_PATTERN,
        ),
        views.CourseGradingPolicy.as_view(), name='course_grading_policy'
    ),
)
