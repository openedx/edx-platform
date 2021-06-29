"""
All tests for applications APIs serializers
"""
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.api.serializers import (
    EducationSerializer,
    ReferenceSerializer,
    WorkExperienceSerializer
)
from openedx.adg.lms.applications.constants import MAX_NUMBER_OF_REFERENCES, MAX_REFERENCE_ERROR_MSG
from openedx.adg.lms.applications.models import Education
from openedx.adg.lms.applications.tests.factories import ReferenceFactory, UserApplicationFactory

# pylint: disable=redefined-outer-name


@pytest.fixture
def user_application(request):
    """
    Create user application, this fixture can be passed as a parameter to other pytests or fixtures
    """
    return UserApplicationFactory(user=UserFactory())


@pytest.fixture
def education_data(request, user_application):
    """
    Data for education serializer
    """
    return {
        'date_started_month': 2,
        'date_started_year': 2017,
        'date_completed_month': 3,
        'date_completed_year': 2018,
        'name_of_school': 'PUCIT',
        'degree': Education.BACHELOR_DEGREE,
        'is_in_progress': True,
        'user_application': user_application.id
    }


@pytest.fixture
def work_experience_data(request, user_application):
    """
    Data for education serializer
    """
    return {
        'date_started_month': 2,
        'date_started_year': 2018,
        'date_completed_month': 8,
        'date_completed_year': 2020,
        'name_of_organization': 'Arbisoft',
        'job_position_title': 'SSE',
        'is_current_position': True,
        'job_responsibilities': 'Testing',
        'user_application': user_application.id
    }


def get_reference_data(user_application):
    """
    Get data for reference serializer
    """
    return {
        'name': 'Test Name',
        'position': 'Test Position',
        'relationship': 'Test Relationship',
        'phone_number': '112233',
        'email': 'test@test.com',
        'user_application': user_application.id
    }


@pytest.mark.django_db
def test_education_serializer_with_invalid_data(education_data):
    """
    Verify the education serializer behavior for invalid data.
    """
    expected_errors = {
        'date_completed_year': [
            'Date completed year isn\'t applicable for degree in progress'
        ],
        'date_completed_month': [
            'Date completed month isn\'t applicable for degree in progress'
        ]
    }
    serializer = EducationSerializer(data=education_data)

    assert not serializer.is_valid()
    assert serializer.errors == expected_errors


@pytest.mark.django_db
def test_education_serializer_with_valid_data(education_data, user_application, request):
    """
    Verify the education serializer behavior for valid data.
    """
    education_data['is_in_progress'] = False
    education_data['area_of_study'] = 'Computer Sciences'
    request.user = user_application.user

    serializer = EducationSerializer(data=education_data, context={'request': request})

    assert serializer.is_valid()
    assert not serializer.errors


@pytest.mark.parametrize(
    'degree, area_of_study, expected_area_of_study', [
        (Education.HIGH_SCHOOL_DIPLOMA, 'Computer Sciences', ''),
        (Education.HIGH_SCHOOL_DIPLOMA, '', ''),
        (Education.BACHELOR_DEGREE, 'Computer Sciences', 'Computer Sciences')
    ]
)
@pytest.mark.django_db
def test_education_serializer_with_valid_degree_data(
    degree,
    area_of_study,
    expected_area_of_study,
    education_data,
    request,
    user_application
):
    """
    Verify the education serializer behavior for different degree values
    """
    education_data['is_in_progress'] = False
    education_data['area_of_study'] = area_of_study
    education_data['degree'] = degree
    request.user = user_application.user

    serializer = EducationSerializer(data=education_data, context={'request': request})

    assert serializer.is_valid()
    assert not serializer.errors
    assert serializer.data['area_of_study'] == expected_area_of_study


@pytest.mark.django_db
def test_work_experience_serializer_with_invalid_data(work_experience_data):
    """
    Verify the work experience serializer behavior for invalid data.
    """
    expected_errors = {
        'date_completed_year': [
            'Date completed year isn\'t applicable for current work experience'
        ],
        'date_completed_month': [
            'Date completed month isn\'t applicable for current work experience'
        ]
    }
    serializer = WorkExperienceSerializer(data=work_experience_data)

    assert not serializer.is_valid()
    assert serializer.errors == expected_errors


@pytest.mark.django_db
def test_work_experience_serializer_with_valid_data(work_experience_data, request, user_application):
    """
    Verify the work experience serializer behavior for valid data.
    """
    work_experience_data['is_current_position'] = False
    request.user = user_application.user

    serializer = WorkExperienceSerializer(data=work_experience_data, context={'request': request})

    assert serializer.is_valid()
    assert not serializer.errors


@pytest.mark.parametrize(
    'is_valid, expected_errors', [
        (True, {}),
        (False, {'user_application': [MAX_REFERENCE_ERROR_MSG]})
    ],
)
@pytest.mark.django_db
def test_reference_serializer_validate_user_application_create(is_valid, expected_errors, user_application, request):
    """
    Test `validate_user_application` method of `ReferenceSerializer` in case of creation

    Test that creation of new references upto the max reference limit against a user application is validated and
    creation of the reference exceeding the max limit is invalidated.
    """
    if is_valid:
        ReferenceFactory.create_batch(MAX_NUMBER_OF_REFERENCES - 1, user_application=user_application)
    else:
        ReferenceFactory.create_batch(MAX_NUMBER_OF_REFERENCES, user_application=user_application)

    reference_data = get_reference_data(user_application)
    request.user = user_application.user

    serializer = ReferenceSerializer(data=reference_data, context={'request': request})

    assert serializer.is_valid() == is_valid
    assert serializer.errors == expected_errors


@pytest.mark.django_db
def test_reference_serializer_validate_user_application_update(user_application, request):
    """
    Test `validate_user_application` method of `ReferenceSerializer` in case of updation

    Test that request for updation of existing reference, i.e. when instance is passed to the serializer, is validated
    even if max reference limit is reached.
    """
    ReferenceFactory.create_batch(MAX_NUMBER_OF_REFERENCES - 1, user_application=user_application)
    reference = ReferenceFactory(user_application=user_application)

    reference_data = get_reference_data(user_application)
    request.user = user_application.user

    serializer = ReferenceSerializer(instance=reference, data=reference_data, context={'request': request})

    assert serializer.is_valid()
    assert not serializer.errors
