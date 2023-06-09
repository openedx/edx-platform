"""
Instructor Tools API endpoint urls.
"""

from django.urls import path
from lms.djangoapps.instructor_tools import api

urlpatterns = [
    path('instructor_tools/api/calculate_all_grades_csv', api.calculate_all_grades_csv, name='calculate_all_grades_csv'),
]