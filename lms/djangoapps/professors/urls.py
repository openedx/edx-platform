"""
URL definitions for the professors
"""

from django.conf.urls import url
from django.conf import settings
from professors.views import professors_index, professors_detail
from professors.api import (
    ProfessorDetailAPIView,
    ProfessorsListAPIView,
    ProfessorCoursesListAPIView,
    CourseProfessorAPIView
)


urlpatterns = [
    url(
        r'^professors/$',
        professors_index,
        name='professor_index'
    ),
    url(
        r'^professors/(?P<pk>[0-9]+)/$',
        professors_detail,
        name='professor_detail'
    ),
]

urlpatterns += [
    url(
        r'api/v1/professors/$',
        ProfessorsListAPIView.as_view(),
        name='api_professors'
    ),
    url(
        r'api/v1/professors/(?P<pk>[0-9]+)/$',
        ProfessorDetailAPIView.as_view(),
        name='api_professor_detail'
    ),
    url(
        r'api/v1/professor/courses/$',
        ProfessorCoursesListAPIView.as_view(),
        name='api_professor_courses'
    ),
    url(
        r'api/v1/course/{}/professor/$'.format(settings.COURSE_ID_PATTERN),
        CourseProfessorAPIView.as_view(),
        name='api_course_professor'
    ),
]
