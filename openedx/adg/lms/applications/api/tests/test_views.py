"""
All tests for applications APIs views
"""
import json

import pytest
from django.urls import reverse
from rest_framework import status

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.api.serializers import EducationSerializer, WorkExperienceSerializer
from openedx.adg.lms.applications.models import Education, WorkExperience
from openedx.adg.lms.applications.tests.factories import EducationFactory, UserApplicationFactory, WorkExperienceFactory

JSON_CONTENT_TYPE = 'application/json'


# pylint: disable=redefined-outer-name, unused-argument

@pytest.fixture
def user_instance(request):
    """
    Create user, this fixture can be passed as a parameter to other pytests or fixtures
    """
    return UserFactory(password='password')


@pytest.fixture
def user_application(request, user_instance):
    """
    Create user application, this fixture can be passed as a parameter to other pytests or fixtures
    """
    return UserApplicationFactory(user=user_instance)


@pytest.fixture
def education_data(request, user_application):
    """
    Create education data, this fixture can be passed as a parameter to other pytests or fixtures
    """
    bachelor_education = EducationFactory(user_application=user_application)
    doctoral_education = EducationFactory(user_application=user_application, degree=Education.DOCTORAL_DEGREE)
    return bachelor_education, doctoral_education


@pytest.fixture
def education_data_for_post_and_patch(request, education_data):
    """
    Create education data, this fixture can be passed as a parameter to other pytests or fixtures
    """
    education, _ = education_data
    return {
        'date_started_month': 2,
        'date_started_year': 2018,
        'date_completed_month': 8,
        'date_completed_year': 2020,
        'name_of_school': 'PUCIT',
        'degree': Education.BACHELOR_DEGREE,
        'area_of_study': 'Computer Sciences',
        'is_in_progress': False,
        'user_application': education.user_application.id
    }


@pytest.fixture
def work_experience_data(request, user_application):
    """
    Create work experience data, this fixture can be passed as a parameter to other pytests or fixtures
    """
    work_experience = WorkExperienceFactory(user_application=user_application)
    sse_work_experience = WorkExperienceFactory(user_application=user_application, job_position_title='SSE')
    return work_experience, sse_work_experience


@pytest.fixture
def work_experience_data_for_post_and_patch(request, work_experience_data):
    """
    Create education data, this fixture can be passed as a parameter to other pytests or fixtures
    """
    work_experience, _ = work_experience_data
    return {
        'date_started_month': 2,
        'date_started_year': 2018,
        'date_completed_month': 8,
        'date_completed_year': 2020,
        'name_of_organization': 'Arbisoft',
        'job_position_title': 'QAE',
        'job_responsibilities': 'Testing',
        'is_current_position': False,
        'user_application': work_experience.user_application.id
    }


@pytest.fixture
def login_client(request, client, user_instance):
    """
    User login fixture. User will be authenticated for all tests where we pass this fixture.
    """
    client.login(username=user_instance.username, password='password')
    return client


@pytest.fixture
def work_experience_not_applicable_api(login_client):
    """
    Get is work experience not applicable data
    """
    def is_work_experience_not_applicable_api(is_not_applicable='true'):
        url = reverse('applications:work_experience-update_is_not_applicable')
        is_work_experience_not_applicable_api_data = {'is_work_experience_not_applicable': is_not_applicable}
        response = login_client.patch(
            url, data=json.dumps(is_work_experience_not_applicable_api_data), content_type=JSON_CONTENT_TYPE
        )
        return response

    return is_work_experience_not_applicable_api


@pytest.mark.django_db
def test_unauthenticated_education_api_call(education_data, client):
    """
    Test education api calls for unauthenticated user.
    """
    url = reverse('applications_api:education-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_education_api_list(education_data, login_client):
    """
    Test education list api call for authenticated user.
    """
    url = reverse('applications_api:education-list')
    response = login_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


@pytest.mark.django_db
def test_education_api_retrieve(education_data, login_client):
    """
    Test education retrieve api call for authenticated user.
    """
    _, expected_education_data = education_data
    url = reverse('applications_api:education-detail', kwargs={'pk': expected_education_data.id})
    response = login_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == EducationSerializer(expected_education_data).data


@pytest.mark.django_db
def test_education_api_valid_post_data(user_instance, login_client, education_data_for_post_and_patch):
    """
    Test education post api call with valid data for authenticated user.
    """
    url = reverse('applications_api:education-list')
    response = login_client.post(
        url, data=json.dumps(education_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert Education.objects.get(pk=response.data['id'])


@pytest.mark.django_db
def test_education_api_invalid_post_data(user_instance, login_client, education_data_for_post_and_patch):
    """
    Test education post api call with invalid data for authenticated user.
    """
    education_data_for_post_and_patch['is_in_progress'] = True
    education_data_for_post_and_patch['date_completed_year'] = 2016

    url = reverse('applications_api:education-list')
    response = login_client.post(
        url, data=json.dumps(education_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_education_api_valid_patch_data(education_data, login_client, education_data_for_post_and_patch):
    """
    Test education patch api call with valid data for authenticated user.
    """
    education, _ = education_data

    education_data_for_post_and_patch['degree'] = Education.MASTERS_DEGREE
    education_data_for_post_and_patch['area_of_study'] = 'Data Sciences'

    url = reverse('applications_api:education-detail', kwargs={'pk': education.id})
    response = login_client.patch(
        url, data=json.dumps(education_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['degree'] == education_data_for_post_and_patch['degree']
    assert response.data['area_of_study'] == education_data_for_post_and_patch['area_of_study']


@pytest.mark.django_db
def test_education_api_invalid_patch_data(education_data, login_client, education_data_for_post_and_patch):
    """
    Test education patch api call with invalid data for authenticated user.
    """
    education, _ = education_data
    education_data_for_post_and_patch['is_in_progress'] = True
    url = reverse('applications_api:education-detail', kwargs={'pk': education.id})
    response = login_client.patch(
        url, data=json.dumps(education_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_education_api_delete(education_data, login_client):
    """
    Test education delete api call for authenticated user.
    """
    _, education = education_data
    url = reverse('applications_api:education-detail', kwargs={'pk': education.id})
    response = login_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_unauthenticated_work_experience_api_call(work_experience_data, client):
    """
    Test work experience api calls for unauthenticated user.
    """
    url = reverse('applications_api:work_experience-list')
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_work_experience_api_list(work_experience_data, login_client):
    """
    Test work experience list api call for authenticated user.
    """
    url = reverse('applications_api:work_experience-list')
    response = login_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2


@pytest.mark.django_db
def test_work_experience_api_retrieve(work_experience_data, login_client):
    """
    Test work experience retrieve api call for authenticated user.
    """
    _, expected_work_experience_data = work_experience_data
    url = reverse('applications_api:work_experience-detail', kwargs={'pk': expected_work_experience_data.id})
    response = login_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data == WorkExperienceSerializer(expected_work_experience_data).data


@pytest.mark.django_db
def test_work_experience_api_valid_post_data(user_instance, login_client, work_experience_data_for_post_and_patch):
    """
    Test work experience post api call with valid data for authenticated user.
    """
    url = reverse('applications_api:work_experience-list')
    response = login_client.post(
        url, data=json.dumps(work_experience_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert WorkExperience.objects.get(pk=response.data['id'])


@pytest.mark.django_db
def test_work_experience_api_invalid_post_data(
    user_instance, login_client, work_experience_data_for_post_and_patch
):
    """
    Test work experience post api call with invalid data for authenticated user.
    """
    work_experience_data_for_post_and_patch['is_current_position'] = True
    url = reverse('applications_api:work_experience-list')
    response = login_client.post(
        url, data=json.dumps(work_experience_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_work_experience_api_valid_patch_data(
    work_experience_data, login_client, work_experience_data_for_post_and_patch
):
    """
    Test work experience patch api call with valid data for authenticated user.
    """
    work_experience, _ = work_experience_data

    work_experience_data_for_post_and_patch['job_position_title'] = 'SSE'
    work_experience_data_for_post_and_patch['job_responsibilities'] = 'Development'

    url = reverse('applications_api:work_experience-detail', kwargs={'pk': work_experience.id})
    response = login_client.patch(
        url, data=json.dumps(work_experience_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data['job_position_title'] == work_experience_data_for_post_and_patch['job_position_title']
    assert response.data['job_responsibilities'] == work_experience_data_for_post_and_patch['job_responsibilities']


@pytest.mark.django_db
def test_work_experience_api_invalid_patch_data(
    work_experience_data, login_client, work_experience_data_for_post_and_patch
):
    """
    Test work experience patch api call with invalid data for authenticated user.
    """
    work_experience, _ = work_experience_data
    work_experience_data_for_post_and_patch['is_current_position'] = True

    url = reverse('applications_api:work_experience-detail', kwargs={'pk': work_experience.id})
    response = login_client.patch(
        url, data=json.dumps(work_experience_data_for_post_and_patch), content_type=JSON_CONTENT_TYPE
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_work_experience_api_delete(work_experience_data, login_client):
    """
    Test work experience delete api call for authenticated user.
    """
    _, work_experience = work_experience_data
    url = reverse('applications_api:work_experience-detail', kwargs={'pk': work_experience.id})
    response = login_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_is_work_experience_not_applicable_api_with_true(work_experience_data, work_experience_not_applicable_api):
    """
    Test the is_work_experience_not_applicable_api with true value
    """
    response = work_experience_not_applicable_api('true')
    assert response.status_code == status.HTTP_200_OK
    assert WorkExperience.objects.count() == 0


@pytest.mark.django_db
def test_is_work_experience_not_applicable_api_with_false(user_application, work_experience_not_applicable_api):
    """
    Test the is_work_experience_not_applicable_api with false value
    """
    response = work_experience_not_applicable_api('false')
    assert response.status_code == status.HTTP_200_OK
