"""
URLs for the Enrollment API

"""
from django.conf import settings
from django.conf.urls import patterns, url

from .views import get_course_enrollment, list_student_enrollments

urlpatterns = []

if settings.FEATURES.get('ENABLE_COMBINED_LOGIN_REGISTRATION'):
    urlpatterns += patterns(
        'enrollment.views',
        url(r'^student$', list_student_enrollments, name='courseenrollments'),
        url(
            r'^course/{course_key}$'.format(course_key=settings.COURSE_ID_PATTERN),
            get_course_enrollment,
            name='courseenrollment'
        ),
    )
