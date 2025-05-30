"""
Contains URLs for the Course Experience API
"""


from django.conf import settings
from django.urls import re_path

from openedx.features.course_experience.api.v1.views import (
    reset_course_deadlines,
    reset_multiple_course_deadlines,
    CourseDeadlinesMobileView,
)

urlpatterns = []

# URL for resetting course deadlines
urlpatterns += [
    re_path(
        r'v1/reset_course_deadlines',
        reset_course_deadlines,
        name='course-experience-reset-course-deadlines'
    ),
    re_path(
        r'v1/reset_multiple_course_deadlines/',
        reset_multiple_course_deadlines,
        name='course-experience-reset-multiple-course-deadlines',
    )
]

# URL for retrieving course deadlines info
urlpatterns += [
    re_path(
        fr'v1/course_deadlines_info/{settings.COURSE_KEY_PATTERN}',
        CourseDeadlinesMobileView.as_view(),
        name='course-experience-course-deadlines-mobile'
    ),
]
