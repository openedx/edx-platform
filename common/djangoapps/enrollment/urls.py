"""
URLs for the Enrollment API

"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import (
    EnrollmentView,
    EnrollmentListView,
    EnrollmentCourseDetailView
)

from openedx.core.djangoapps.appsembler.msft_lp.views import AppsemblerEnrollmentListView

# import API views here

urlpatterns = patterns(
    'enrollment.views',
    url(
        r'^enrollment/{username},{course_key}$'.format(
            username=settings.USERNAME_PATTERN, course_key=settings.COURSE_ID_PATTERN
        ),
        EnrollmentView.as_view(),
        name='courseenrollment'
    ),
    url(
        r'^enrollment/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(),
        name='courseenrollment'
    ),
    # url(r'^enrollment$', EnrollmentListView.as_view(), name='courseenrollments'),
    # Appsembler specific: Original view commented in favor of our override of
    # the view, that changes the org to Microsoft if the course is set as
    # Microsoft course in advanced settings. Feature for MSFT LP only.
    url(r'^enrollment$', AppsemblerEnrollmentListView.as_view(), name='courseenrollments'),
    url(
        r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
        EnrollmentCourseDetailView.as_view(),
        name='courseenrollmentdetails'
    ),
)
