"""
URLs for the Enrollment API

"""
from django.conf.urls import patterns, url

from .views import get_course_enrollment, list_student_enrollments

urlpatterns = patterns(
    'enrollment.views',
    url(r'^(?P<username>[\w.+-]+)$', list_student_enrollments, name='courseenrollments'),
    url(
        r'^(?P<username>[\w.+-]+)/course/(?P<course_id>[\w.+-]+)$', get_course_enrollment, name='courseenrollment'
    ),
)
