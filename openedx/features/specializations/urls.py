"""
All urls for specializations app
"""
from django.conf.urls import url

from .views import enroll_in_all_specialisation_courses, list_specializations, specialization_about

urlpatterns = [
    url(r'^specializations/$', list_specializations, name='list_specializations'),
    url(r'^specializations/(?P<specialization_uuid>[0-9a-f-]{36})$', specialization_about, name='specialization_about'),
    url(
        r'^specialisation_enrollment/(?P<specialization_uuid>[0-9a-f-]{36})$',
        enroll_in_all_specialisation_courses,
        name='enroll_in_all_specialisation_courses'
    ),
]
