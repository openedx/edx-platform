"""
Learner Dashboard API v0 URLs.
"""

from django.urls import re_path

from lms.djangoapps.learner_dashboard.api.v0.views import ProgramProgressDetailView

app_name = 'v0'
urlpatterns = [
    re_path(r'^programs/(?P<program_uuid>[0-9a-f-]+)/progress_details/$', ProgramProgressDetailView.as_view(),
            name='program_progress_detail'),
]
