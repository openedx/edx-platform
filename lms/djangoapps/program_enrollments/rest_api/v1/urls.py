""" Program Enrollments API v1 URLs. """


from django.conf import settings
from django.conf.urls import url

from openedx.core.constants import COURSE_ID_PATTERN

from .constants import PROGRAM_UUID_PATTERN
from .views import (
    EnrollmentDataResetView,
    ProgramCourseEnrollmentOverviewView,
    ProgramCourseEnrollmentsView,
    ProgramCourseGradesView,
    ProgramEnrollmentsView,
    UserProgramCourseEnrollmentView,
    UserProgramReadOnlyAccessView
)

app_name = 'v1'

urlpatterns = [
    url(
        r'^programs/enrollments/$',
        UserProgramReadOnlyAccessView.as_view(),
        name='learner_program_enrollments'
    ),
    url(
        r'^programs/readonly_access/$',
        UserProgramReadOnlyAccessView.as_view(),
        name='user_program_readonly_access'
    ),
    url(
        r'^programs/{program_uuid}/enrollments/$'.format(program_uuid=PROGRAM_UUID_PATTERN),
        ProgramEnrollmentsView.as_view(),
        name='program_enrollments'
    ),
    url(
        r'^programs/{program_uuid}/courses/{course_id}/enrollments/'.format(
            program_uuid=PROGRAM_UUID_PATTERN,
            course_id=COURSE_ID_PATTERN
        ),
        ProgramCourseEnrollmentsView.as_view(),
        name="program_course_enrollments"
    ),
    url(
        r'^programs/{program_uuid}/courses/{course_id}/grades/'.format(
            program_uuid=PROGRAM_UUID_PATTERN,
            course_id=COURSE_ID_PATTERN
        ),
        ProgramCourseGradesView.as_view(),
        name="program_course_grades"
    ),
    url(
        r'^programs/{program_uuid}/overview/'.format(
            program_uuid=PROGRAM_UUID_PATTERN,
        ),
        ProgramCourseEnrollmentOverviewView.as_view(),
        name="program_course_enrollments_overview"
    ),
    url(
        r'^users/{username}/programs/{program_uuid}/courses'.format(
            username=settings.USERNAME_PATTERN,
            program_uuid=PROGRAM_UUID_PATTERN,
        ),
        UserProgramCourseEnrollmentView.as_view(),
        name="user_program_course_enrollments"
    ),
    url(
        r'^integration-reset',
        EnrollmentDataResetView.as_view(),
        name="reset_enrollment_data",
    )
]
