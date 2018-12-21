"""
URL definitions for the professors
"""

from django.conf.urls import url
from professors.views import professors_index, professors_detail
from professors.api import ProfessorDetailAPIView, ProfessorsListAPIView


urlpatterns = [
    url(
        r'^professors/',
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
]