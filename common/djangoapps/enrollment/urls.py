"""
URLs for the Enrollment API

"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import EnrollmentView, EnrollmentListView, EnrollmentListRedirectView, EnrollmentRedirectView

urlpatterns = []
STUDENT_PATTERN = '(?P<student>[\w.+-]+)'

if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    urlpatterns += patterns(
        'enrollment.views',
        url(r'^student/{student}$'.format(student=STUDENT_PATTERN), EnrollmentListView.as_view(), name='courseenrollments'),
        url(r'^student$', EnrollmentListRedirectView.as_view(), name='courseenrollmentsredirect'),
        url(
            r'^student/{student}/course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN, student=STUDENT_PATTERN),
            EnrollmentView.as_view(),
            name='courseenrollment'
        ),
        url(
            r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
            EnrollmentRedirectView.as_view(),
            name='courseenrollmentredirect'
        ),
    )
