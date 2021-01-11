"""
All tests for applications APIs serializers
"""
import pytest

from common.djangoapps.student.tests.factories import UserFactory

from ..models import Education
from ..serializers import EducationSerializer, WorkExperienceSerializer
from .factories import UserApplicationFactory


@pytest.fixture
def user_application(request):
    """
    Create user application, this fixture can be passed as a parameter to other pytests or fixtures
    """
    return UserApplicationFactory(user=UserFactory())


@pytest.fixture
def education_data(request, user_application):  # pylint: disable=redefined-outer-name
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
def work_experience_data(request, user_application):  # pylint: disable=redefined-outer-name
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


@pytest.mark.django_db
def test_education_serializer_with_invalid_data(education_data):  # pylint: disable=redefined-outer-name
    """
    Verify the education serializer behavior for invalid data.
    """
    expected_errors = {
        'date_completed_year': [
            'Date completed year isn\'t applicable for degree in progress'
        ],
        'date_completed_month': [
            'Date completed month isn\'t applicable for degree in progress'
        ],
        'area_of_study': [
            'Area of study is required for all degrees above High School Diploma'
        ]
    }
    serializer = EducationSerializer(data=education_data)

    assert not serializer.is_valid()
    assert serializer.errors == expected_errors


@pytest.mark.django_db
def test_education_serializer_with_valid_data(education_data):  # pylint: disable=redefined-outer-name
    """
    Verify the education serializer behavior for valid data.
    """
    education_data['is_in_progress'] = False
    education_data['area_of_study'] = 'Computer Sciences'

    serializer = EducationSerializer(data=education_data)

    assert serializer.is_valid()
    assert not serializer.errors


@pytest.mark.django_db
def test_education_serializer_with_valid_degree_data(education_data):  # pylint: disable=redefined-outer-name
    """
    Verify the education serializer behavior for different degree values
    """
    education_data['is_in_progress'] = False
    education_data['area_of_study'] = 'Computer Sciences'
    serializer = EducationSerializer(data=education_data)

    assert serializer.is_valid()
    assert not serializer.errors
    assert serializer.data['area_of_study'] == 'Computer Sciences'

    education_data['degree'] = Education.HIGH_SCHOOL_DIPLOMA
    serializer = EducationSerializer(data=education_data)

    assert serializer.is_valid()
    assert not serializer.data['area_of_study']


@pytest.mark.django_db
def test_work_experience_serializer_with_invalid_data(work_experience_data):  # pylint: disable=redefined-outer-name
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
def test_work_experience_serializer_with_valid_data(work_experience_data):  # pylint: disable=redefined-outer-name
    """
    Verify the work experience serializer behavior for valid data.
    """
    work_experience_data['is_current_position'] = False
    serializer = WorkExperienceSerializer(data=work_experience_data)

    assert serializer.is_valid()
    assert not serializer.errors
