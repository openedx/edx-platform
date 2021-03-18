"""
All tests for specializations views
"""
import pytest
from django.http import HttpResponse
from django.urls import reverse
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.core.djangolib.testing.philu_utils import intercept_renderer
from openedx.features.philu_courseware.models import CourseEnrollmentMeta
from openedx.features.specializations.tests.mock_get_program_helpers import mock_get_program
from student.tests.factories import CourseEnrollmentFactory

from .factories import CourseEnrollmentMetaFactory

_specialization_uuid = 'eb228773-a9a5-48cf-bb0e-94725d5aa4f1'


# pylint: disable=redefined-outer-name

@pytest.fixture()
def specialization_about_path():
    """
    Fixture for path specialisation about page
    """
    return reverse('specialization_about', kwargs={
        'specialization_uuid': _specialization_uuid
    })


@pytest.fixture()
def specialization_enrollment_path():
    """
    Fixture for path to enroll in all specialisation courses url
    """
    return reverse('enroll_in_all_specialisation_courses', kwargs={
        'specialization_uuid': _specialization_uuid
    })


@pytest.fixture()
def logged_client(client):
    """
    Fixture a logged in client
    """
    client.login(
        username=UserFactory().username, password=UserFactory._DEFAULT_PASSWORD  # pylint: disable=protected-access
    )
    return client


@pytest.mark.django_db
def test_specialization_about_page_no_courses(mocker, client, specialization_about_path):
    """
    Test specialization about page when there is no course
    """
    mocker.patch('openedx.features.specializations.views.render_to_response', intercept_renderer)
    mocker.patch(
        'openedx.features.specializations.views.get_program_courses',
        return_value=(mock_get_program(), [])
    )

    response = client.get(specialization_about_path)
    assert response.status_code == 200
    assert response.mako_context['show_course_status'] is False
    assert not response.mako_context['courses']


@pytest.mark.django_db
@pytest.mark.parametrize('courses, show_course_status', [
    pytest.param([{'enrolled': True, 'completed': True, 'course_id': ''}, ], True, id="completed_course"),
    pytest.param([{'enrolled': True, }, {'enrolled': False, }, ], False, id="only_one_enrolled_course"),
    pytest.param(
        [{'enrolled': True, }, {'enrolled': True, 'course_id': CourseKey.from_string('dummy/course/id')}, ],
        False, id="only_one_linked_course"
    )
])
def test_specialization_about_page_with_courses(courses, show_course_status, mocker, client, specialization_about_path):
    """
    Test specialization about page when there with existing course
    """
    for course in courses:
        if course.get('course_id'):
            continue

        course_enrollment_meta = CourseEnrollmentMetaFactory(program_uuid=_specialization_uuid)
        course.update({
            'course_id': course_enrollment_meta.course_enrollment.course_id
        })

    mocked_render_to_response = mocker.patch(
        'openedx.features.specializations.views.render_to_response',
        return_value=HttpResponse()
    )
    mocker.patch(
        'openedx.features.specializations.views.get_program_courses',
        return_value=({}, courses)
    )

    client.get(specialization_about_path)

    mocked_render_to_response.assert_called_once_with('features/specializations/about.html', {
        'show_course_status': show_course_status
    })


@pytest.mark.django_db
def test_enroll_in_all_specialisation_courses_for_completed_courses(logged_client, mocker,
                                                                    specialization_enrollment_path):
    """
    Test enrollment in specialization courses when course are already completed
    """
    mocker.patch(
        'openedx.features.specializations.views.get_program_courses',
        return_value=({}, [{'enrolled': True, 'completed': True}, ])
    )

    response = logged_client.post(specialization_enrollment_path)

    assert response.status_code == 200


@pytest.mark.django_db
def test_enroll_in_all_specialisation_courses_not_enrolled_courses(logged_client, mocker,
                                                                   specialization_enrollment_path):
    """
    Test enrollment in specialization courses when no course previously enrolled
    """
    mocked_log_info = mocker.patch('openedx.features.specializations.views.log.info')
    mocker.patch(
        'openedx.features.specializations.views.get_program_courses',
        return_value=({}, [{'enrolled': False, 'completed': True, 'key': 'dummy/123/key'}, ])
    )
    mocker.patch(
        'openedx.features.specializations.views.change_enrollment',
        return_value=HttpResponse(status=500)
    )

    response = logged_client.post(specialization_enrollment_path)

    mocked_log_info.assert_called_once_with('Course dummy/123/key enrollment request ended with status 500')
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize('is_enrolled', (True, False), ids=["create_linkage", "do_not_linkage"])
def test_enroll_in_all_specialisation_courses_not_completed(is_enrolled, client, mocker,
                                                            specialization_enrollment_path):
    """
    Test enrollment in specialization courses when some or all courses were previously enrolled
    but were not complete
    """
    user = UserFactory()
    client.login(username=user.username, password=UserFactory._DEFAULT_PASSWORD)  # pylint: disable=protected-access
    enrollment = CourseEnrollmentFactory(user=user, is_active=is_enrolled)
    mocker.patch(
        'openedx.features.specializations.views.get_program_courses',
        return_value=({}, [{'enrolled': True, 'completed': False, 'course_id': enrollment.course_id}, ])
    )
    mocker.patch('openedx.features.specializations.views.change_enrollment', return_value=HttpResponse(status=500))

    response = client.post(specialization_enrollment_path)

    is_linked = CourseEnrollmentMeta.objects.filter(
        course_enrollment=enrollment, program_uuid=_specialization_uuid
    ).exists()
    assert response.status_code == 200
    assert is_linked is is_enrolled
