"""
URLs for the Enrollment API

"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import EnrollmentView, EnrollmentListView

urlpatterns = []

if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    urlpatterns += patterns(
        'enrollment.views',
        url(r'^student$', EnrollmentListView.as_view(), name='courseenrollments'),
        url(
            r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
            EnrollmentView.as_view(),
            name='courseenrollment'
        ),
    )
