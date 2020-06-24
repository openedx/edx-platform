"""
Contains URLs for the Course Experience API
"""


from django.urls import re_path

from openedx.features.course_experience.api.v1.views import reset_course_deadlines

urlpatterns = []

# URL for resetting course deadlines
urlpatterns += [
    re_path(
        r'v1/reset_course_deadlines',
        reset_course_deadlines,
        name='course-experience-reset-course-deadlines'
    ),
]
