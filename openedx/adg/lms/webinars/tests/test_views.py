"""
All test cases for webinars app views
"""

import mock
import pytest
from django.urls import reverse

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.webinars.models import Webinar, WebinarRegistration
from openedx.adg.lms.webinars.tests.factories import WebinarFactory, WebinarRegistrationFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name='user_client')
def user_client_login(request, client):
    """
    User and client login fixture. User will be authenticated for all tests where we pass this fixture.
    """
    user = UserFactory()
    client.login(username=user.username, password='test')
    return user, client


def test_webinar_registration_view_object_does_not_exist(user_client):
    """
    Test webinar registration if webinar does not exist
    """
    _, client = user_client

    response = client.post(reverse('webinar_registration', kwargs={'pk': 100, 'action': 'register'}))

    assert response.status_code == 404


def test_webinar_description_view_invalid_pk(user_client):
    """
    Test webinar description with invalid pk
    """
    _, client = user_client
    response = client.get(reverse('webinar_event', kwargs={'pk': 999}))
    assert response.status_code == 404


@mock.patch('django.template.response.select_template')
def test_webinar_description_view_valid_pk(mock_select_template, user_client):
    """
    Test webinar description with valid pk
    """
    _, client = user_client
    webinar = WebinarFactory(status=Webinar.CANCELLED)

    client.get(reverse('webinar_event', kwargs={'pk': webinar.id}))

    mock_select_template.assert_called_once_with(
        ['adg/lms/webinar/description_page.html'], using=None
    )


def test_webinar_registration_view_cancelled_webinar(client, user_client):
    """
    Test webinar registration if webinar is cancelled
    """
    _, client = user_client
    webinar = WebinarFactory(status=Webinar.CANCELLED)

    response = client.post(reverse('webinar_registration', kwargs={'pk': webinar.id, 'action': 'register'}))

    assert response.status_code == 500


@pytest.mark.parametrize('action', ['register', 'cancel'])
def test_webinar_registration_view_register_user_with_no_prior_registration(action, user_client, mocker):
    """
    Test webinar registration and cancellation if webinar was not previously registered by user
    """
    mock_send_registration_email = mocker.patch('openedx.adg.lms.webinars.views.send_webinar_registration_email')
    webinar = WebinarFactory(status=Webinar.UPCOMING)
    user, client = user_client

    client.post(reverse('webinar_registration', kwargs={'pk': webinar.id, 'action': action}))

    if action == 'register':
        mock_send_registration_email.assert_called_once_with(webinar, user.email)
    else:
        mock_send_registration_email.assert_not_called()


@pytest.mark.parametrize('action', ['register', 'cancel'])
@pytest.mark.parametrize('is_registered', [True, False])
def test_webinar_registration_view_register_user_with_prior_registration(action, user_client, is_registered, mocker):
    """
    Test webinar registration and cancellation if webinar was previously registered or canceled by user
    """
    mock_send_registration_email = mocker.patch('openedx.adg.lms.webinars.views.send_webinar_registration_email')
    user, client = user_client
    registration = WebinarRegistrationFactory(user=user, is_registered=is_registered)

    client.post(reverse('webinar_registration', kwargs={'pk': registration.webinar.id, 'action': action}))

    expected_registration = WebinarRegistration.objects.filter(webinar=registration.webinar, user=user).first()
    assert expected_registration.is_registered == (action == 'register')
    if action == 'register' and not is_registered:
        mock_send_registration_email.assert_called_once_with(registration.webinar, user.email)
    else:
        mock_send_registration_email.assert_not_called()
