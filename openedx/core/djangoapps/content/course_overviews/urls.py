"""
Course API URLs
"""
from django.conf.urls import patterns, url

from .views import GetCoursesEnrollmentEndDate


urlpatterns = patterns(
    '',
    url(r'enrollment_dates/', GetCoursesEnrollmentEndDate.as_view(), name="courses-enrollment-date"),
)
