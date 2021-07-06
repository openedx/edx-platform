"""
All test cases for webinars app views
"""
import pytest
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

from openedx.adg.lms.webinars.models import WebinarRegistration
from openedx.adg.lms.webinars.tests.factories import WebinarFactory, WebinarRegistrationFactory

pytestmark = pytest.mark.django_db


def test_webinar_registration_view_object_does_not_exist(user_client):
    """
    Test webinar registration if webinar does not exist
    """
    _, client = user_client

    response = client.post(reverse('webinars_api:webinar_registration', kwargs={'pk': 100, 'action': 'register'}))

    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_webinar_registration_view_cancelled_webinar(client, user_client):
    """
    Test webinar registration if webinar is cancelled
    """
    _, client = user_client
    webinar = WebinarFactory(is_cancelled=True)

    response = client.post(
        reverse('webinars_api:webinar_registration', kwargs={'pk': webinar.id, 'action': 'register'})
    )

    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_webinar_registration_view_not_published_webinar(client, user_client, draft_webinar):
    """
    Test webinar registration if webinar is not published
    """
    _, client = user_client

    response = client.post(
        reverse('webinars_api:webinar_registration', kwargs={'pk': draft_webinar.id, 'action': 'register'})
    )

    assert response.status_code == HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.parametrize('action', ['register', 'cancel'])
def test_webinar_registration_view_register_user_with_no_prior_registration(action, user_client, webinar, mocker):
    """
    Test webinar registration and cancellation if webinar was not previously registered by user
    """
    mock_send_registration_email = mocker.patch('openedx.adg.lms.webinars.api.views.send_webinar_registration_email')
    user, client = user_client

    response = client.post(reverse('webinars_api:webinar_registration', kwargs={'pk': webinar.id, 'action': action}))

    if action == 'register':
        mock_send_registration_email.assert_called_once_with(webinar, user.email)
    else:
        mock_send_registration_email.assert_not_called()

    assert response.status_code == HTTP_200_OK


@pytest.mark.parametrize('action', ['register', 'cancel'])
@pytest.mark.parametrize('is_registered', [True, False])
def test_webinar_registration_view_register_user_with_prior_registration(action, user_client, is_registered, mocker):
    """
    Test webinar registration and cancellation if webinar was previously registered or canceled by user
    """
    mock_send_registration_email = mocker.patch('openedx.adg.lms.webinars.api.views.send_webinar_registration_email')
    user, client = user_client
    registration = WebinarRegistrationFactory(user=user, is_registered=is_registered)

    response = client.post(
        reverse('webinars_api:webinar_registration', kwargs={'pk': registration.webinar.id, 'action': action})
    )

    expected_registration = WebinarRegistration.objects.filter(webinar=registration.webinar, user=user).first()
    assert expected_registration.is_registered == (action == 'register')
    if action == 'register' and not is_registered:
        mock_send_registration_email.assert_called_once_with(registration.webinar, user.email)
    else:
        mock_send_registration_email.assert_not_called()

    assert response.status_code == HTTP_200_OK
