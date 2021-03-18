"""
All tests for specializations helpers
"""
import pytest
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.models import CertificateStatuses
from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.specializations import helpers as specializations_helper
from student.tests.factories import CourseEnrollmentFactory

_specialization_uuid = 'eb228773-a9a5-48cf-bb0e-94725d5aa4f1'


@pytest.mark.django_db
def test_get_program_courses_user_not_authenticated(mocker):
    """
    Test program courses data when user is not authenticated
    """
    mocker.patch.object(specializations_helper, 'get_program_from_discovery', return_value={})

    context, courses = specializations_helper.get_program_courses(
        mocker.Mock(is_authenticated=False),
        _specialization_uuid
    )

    assert context == {}
    assert courses == []


@pytest.mark.django_db
@pytest.mark.parametrize('program_context', (
    {}, {'courses': []}, {'courses': [{'course_runs': []}]}
), ids=['no_courses', 'empty_course', 'empty_course_run'])
def test_get_program_courses_user_authenticated_empty_data(program_context, mocker):
    """
    Test program courses data when user is authenticated but courses and course runs are empty
    """
    mocker.patch.object(specializations_helper, 'get_program_from_discovery', return_value=program_context)

    context, courses = specializations_helper.get_program_courses(UserFactory(), _specialization_uuid)

    program_context.update({'courses': []})
    assert context == program_context
    assert courses == []


@pytest.mark.django_db
@pytest.mark.parametrize('program_context, is_course_run_enrolled', (
    ({'courses': [{'course_runs': {'key': 'course/key/123'}}]}, True),
    ({'courses': [{'course_runs': {'key': 'course/key/123'}}]}, False)
), ids=['enrolled_course_run', 'not_enrolled_course_run'])
def test_get_program_courses_user_authenticated_with_data(program_context, is_course_run_enrolled, mocker):
    """
    Test program courses data when user is authenticated but courses and course runs are not empty
    """
    user = UserFactory()
    courses = program_context.get('courses')
    course_run = courses[0].get('course_runs')
    course_id = CourseKey.from_string(course_run['key'])
    CourseEnrollmentFactory(user=user, course_id=course_id, is_active=is_course_run_enrolled)
    mocker.patch.object(specializations_helper, 'get_open_course_rerun', return_value=course_run)
    mocker.patch.object(specializations_helper, 'get_program_from_discovery', return_value=program_context)

    context, courses = specializations_helper.get_program_courses(user, _specialization_uuid)

    course_run['course_id'] = course_id
    course_run['enrolled'] = is_course_run_enrolled
    program_context.update({'courses': [course_run]})
    assert context == program_context
    assert courses == [course_run]


@pytest.mark.django_db
@pytest.mark.parametrize('course_reruns, expected_index, is_open', (
    ([{'enrollment_start': None, 'enrollment_end': None}], 0, False),
    ([{'enrollment_start': '2035-04-07T05:49:41Z', 'enrollment_end': '2036-04-07T05:49:41Z'}], 0, False),
    ([{'enrollment_start': '2012-04-07T05:49:41Z', 'enrollment_end': '2013-04-07T05:49:41Z'}], 0, False),
    ([
        {
            'enrollment_start': specializations_helper.date_time_from_now(-10),
            'enrollment_end': specializations_helper.date_time_from_now(10)
        },
        {
            'enrollment_start': specializations_helper.date_time_from_now(-20),
            'enrollment_end': specializations_helper.date_time_from_now(10)
        }
    ], 1, True),
), ids=['no_dates', 'future', 'closed', 'two_open_runs'])
def test_get_open_course_rerun(course_reruns, expected_index, is_open):
    """
    Test data contained in open course rerun, when enrollment dates are in past, future and present
    """
    course_rerun = specializations_helper.get_open_course_rerun(course_reruns)

    course_reruns[expected_index]['opened'] = is_open
    assert course_rerun == course_reruns[expected_index]


@pytest.mark.django_db
@pytest.mark.parametrize('cert_info, expected_is_completed, expected_is_in_progress, percent', (
    ({'status': CertificateStatuses.downloadable}, True, False, 0.0),
    ({'status': CertificateStatuses.unavailable}, False, True, 10.0),
    ({'status': CertificateStatuses.unavailable}, True, False, 100.0),
), ids=['have_certificate_but_less_progress', 'no_certificate_but_progress_complete', 'course_complete_grades_passed'])
def test_is_course_completed_or_in_progress(cert_info, expected_is_completed, expected_is_in_progress, percent, mocker):
    """
    Test status of course run, when it is complete and when it is in progress
    """
    course_id = CourseKey.from_string('course/test/123')
    CourseOverviewFactory(id=course_id)
    mocker.patch.object(specializations_helper, 'cert_info', return_value=cert_info)
    mock_grades = mocker.patch.object(specializations_helper.CourseGradeFactory, 'read')
    mock_grades().passed = expected_is_completed
    mock_grades().percent = percent

    is_completed, is_in_progress = specializations_helper.is_course_completed_or_in_progress(course_id, UserFactory())

    assert is_completed == expected_is_completed
    assert is_in_progress == expected_is_in_progress


@pytest.mark.django_db
def test_get_program_from_discovery_successfully(mocker):
    """
    Test data received from discovery client
    """
    mocked_client = mocker.patch.object(specializations_helper, 'DiscoveryClient')
    mocked_client().get_program.return_value = 'test data'

    program_context = specializations_helper.get_program_from_discovery(None)

    assert program_context == 'test data'
