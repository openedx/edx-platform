"""
Learner Dashboard API v0 URLs.
"""

from django.urls import re_path

from lms.djangoapps.learner_dashboard.api.v0.views import (
    Programs,
    ProgramProgressDetailView,
    CourseRecommendationApiView
)

UUID_REGEX_PATTERN = r'[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?4[0-9a-fA-F]{3}-?[89abAB][0-9a-fA-F]{3}-?[0-9a-fA-F]{12}'

app_name = 'v0'
urlpatterns = [
    re_path(r'^recommendation/courses/$', CourseRecommendationApiView.as_view(), name='courses'),
    re_path(
        fr'^programs/(?P<enterprise_uuid>{UUID_REGEX_PATTERN})/$',
        Programs.as_view(),
        name='program_list'
    ),
    re_path(r'^programs/(?P<program_uuid>[0-9a-f-]+)/progress_details/$', ProgramProgressDetailView.as_view(),
            name='program_progress_detail'),
]
