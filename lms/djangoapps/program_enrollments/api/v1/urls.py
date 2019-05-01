""" Program Enrollments API v1 URLs. """
from django.conf.urls import url

from lms.djangoapps.program_enrollments.api.v1.constants import PROGRAM_UUID_PATTERN
from lms.djangoapps.program_enrollments.api.v1.views import ProgramEnrollmentsView, ProgramCourseEnrollmentsView
from openedx.core.constants import COURSE_ID_PATTERN


app_name = 'lms.djangoapps.program_enrollments'

urlpatterns = [
    url(
        r'^programs/{program_key}/enrollments/$'.format(program_key=r'(?P<program_key>[0-9a-fA-F-]+)'),
        ProgramEnrollmentsView.as_view(),
        name='program_enrollments'
    ),
    url(
        r'^programs/{program_uuid}/course/{course_id}/enrollments/'.format(
            program_uuid=PROGRAM_UUID_PATTERN,
            course_id=COURSE_ID_PATTERN
        ),
        ProgramCourseEnrollmentsView.as_view(),
        name="program_course_enrollments"
    ),
]
