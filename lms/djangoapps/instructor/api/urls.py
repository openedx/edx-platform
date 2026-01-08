"""
URL configurations for Instructor Dashboard API v2.
"""

from django.urls import re_path

from lms.djangoapps.instructor.api import views
from openedx.core.constants import COURSE_ID_PATTERN

urlpatterns = [
    # ORA Assessments endpoints
    re_path(rf'^courses/{COURSE_ID_PATTERN}/ora', views.ORAAssessmentsView.as_view(), name='ora_assessments'),
]
