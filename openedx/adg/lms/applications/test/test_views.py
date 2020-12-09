"""
Tests for all the views in applications app.
"""
from datetime import date

import mock
import pytest
from django.test import Client, RequestFactory
from django.urls import reverse

from openedx.adg.lms.applications.views import ApplicationHubView, ApplicationSuccessView
from student.tests.factories import UserFactory

from .constants import PASSWORD, USERNAME
from .factories import ApplicationHubFactory


@pytest.mark.django_db
@pytest.fixture(name='user')
def user_fixture():
    """
    Create a test user and their corresponding ApplicationHub object

    Returns:
        User object
    """
    user = UserFactory(username=USERNAME, password=PASSWORD)
    ApplicationHubFactory(user=user)
    return user


@pytest.fixture(scope='module', name='request_factory')
def request_factory_fixture():
    """
    Returns the request factory to make requests.

    Returns:
         RequestFactory object
    """
    return RequestFactory()


@pytest.fixture(name='application_hub_view_get_request')
def application_hub_view_get_request_fixture(request_factory, user):
    """
    Return a HttpRequest object for application hub get

    Args:
        request_factory (RequestFactory): factory to make requests
        user (User): The user that is logged in

    Returns:
        HttpRequest object
    """
    request = request_factory.get(reverse('application_hub'))
    request.user = user
    return request


@pytest.fixture(name='logged_in_client')
def logged_in_client_fixture(user):
    """
    Return a logged in client

    Args:
        user (User): user to log in

    Returns:
        Client() object with logged in user
    """
    client = Client()
    client.login(username=user.username, password=PASSWORD)
    return client


@pytest.mark.django_db
def test_get_redirects_without_login_for_application_hub_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    response = Client().get(reverse('application_hub'))
    assert '/login?next=/application/' in response.url


@pytest.mark.django_db
def test_post_user_redirects_without_login_for_application_hub_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    response = Client().post(reverse('application_hub'))
    assert '/login?next=/application/' in response.url


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.render')
def test_get_initial_application_state_for_application_hub_view(mock_render, application_hub_view_get_request):
    """
    Test the case where the user has not completed even a single objective of the application.
    """
    ApplicationHubView.as_view()(application_hub_view_get_request)

    expected_context = {
        'user_application_hub': application_hub_view_get_request.user.application_hub,
        'pre_req_courses': []
    }
    mock_render.assert_called_once_with(
        application_hub_view_get_request, 'adg/lms/applications/hub.html', context=expected_context
    )


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.render')
def test_get_written_application_completed_state_for_application_hub_view(
        mock_render, application_hub_view_get_request):
    """
    Test the case where the user has completed the written application but not the pre_req courses.
    """
    ApplicationHubView.as_view()(application_hub_view_get_request)

    expected_context = {
        'user_application_hub': application_hub_view_get_request.user.application_hub,
        'pre_req_courses': []
    }
    mock_render.assert_called_once_with(
        application_hub_view_get_request, 'adg/lms/applications/hub.html', context=expected_context
    )


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.render')
def test_get_pre_req_courses_passed_state_for_application_hub_view(mock_render, application_hub_view_get_request):
    """
    Test the case where the user has completed the pre_req courses but not the written application.
    """
    ApplicationHubView.as_view()(application_hub_view_get_request)

    user = application_hub_view_get_request.user
    user.application_hub.set_is_prerequisite_courses_passed()
    expected_context = {
        'user_application_hub': user.application_hub,
        'pre_req_courses': []
    }
    mock_render.assert_called_once_with(
        application_hub_view_get_request, 'adg/lms/applications/hub.html', context=expected_context
    )


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.render')
def test_get_complete_application_done_state_for_application_hub_view(mock_render, application_hub_view_get_request):
    """
    Test the case where the user has completed both objectives i.e the pre_req courses and the
    written application.
    """

    ApplicationHubView.as_view()(application_hub_view_get_request)

    expected_context = {
        'user_application_hub': application_hub_view_get_request.user.application_hub,
        'pre_req_courses': []
    }
    mock_render.assert_called_once_with(
        application_hub_view_get_request, 'adg/lms/applications/hub.html', context=expected_context
    )


@pytest.mark.django_db
def test_get_already_submitted_application_state_for_application_hub_view(application_hub_view_get_request):
    """
    Test the case where the user does not even have a corresponding application.
    """
    application_hub_view_get_request.user.application_hub.submit_application_for_current_date()

    response = ApplicationHubView.as_view()(application_hub_view_get_request)
    assert response.get('Location') == reverse('application_success')
    assert response.status_code == 302


@pytest.mark.django_db
def test_post_logged_in_user_without_required_objectives_completed_for_application_hub_view(logged_in_client):
    """
    Test the case where an authenticated user hits the url without having completed the required objectives i.e
    the pre_req courses and the written application.
    """
    response = logged_in_client.post(reverse('application_hub'))
    assert response.status_code == 400


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.send_application_submission_confirmation_email')
def test_post_logged_in_user_with_required_objectives_completed_to_application_hub_view(
        mock_send_mail, user, logged_in_client):
    """
    Test the case where an authenticated user, with all the required objectives completed, hits the url.
    """
    user.application_hub.set_is_prerequisite_courses_passed()
    user.application_hub.set_is_written_application_completed()

    response = logged_in_client.post(reverse('application_hub'))
    assert mock_send_mail.called
    assert ApplicationHubFactory(user=user).is_application_submitted
    assert ApplicationHubFactory(user=user).submission_date == date.today()
    assert response.get('Location') == reverse('application_success')
    assert response.status_code == 302


@pytest.mark.django_db
def test_post_already_submitted_application_to_application_hub_view(user, logged_in_client):
    """
    Test the case where a user with already submitted application hits the url again.
    """
    user.application_hub.set_is_prerequisite_courses_passed()
    user.application_hub.set_is_written_application_completed()
    user.application_hub.submit_application_for_current_date()

    response = logged_in_client.post(reverse('application_hub'))
    assert response.status_code == 302
    assert response.get('Location') == reverse('application_success')


# ------- Application Success View tests below -------


@pytest.fixture(name='get_request_for_application_success_view')
def get_request_for_application_success_view_fixture(request_factory, user):
    """
    Create a get request for the application_success url.
    """
    request = request_factory.get(reverse('application_success'))
    request.user = user
    return request


@pytest.mark.django_db
def test_get_environment_in_context_for_application_success_view(get_request_for_application_success_view):
    """
    Test if the context contains all the necessary pieces.
    """
    get_request_for_application_success_view.user.application_hub.submit_application_for_current_date()

    response = ApplicationSuccessView.as_view()(get_request_for_application_success_view)
    assert 'submission_date' in response.context_data


@pytest.mark.django_db
def test_get_unauthenticated_user_redirects_for_application_success_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    response = Client().get(reverse('application_success'))
    assert '/login?next=/application/success' in response.url


@pytest.mark.django_db
def test_get_submission_date_for_application_success_view(get_request_for_application_success_view):
    """
    Test if the right date is being fed to the context dictionary.
    """
    user_application_hub = get_request_for_application_success_view.user.application_hub
    user_application_hub.submit_application_for_current_date()

    response = ApplicationSuccessView.as_view()(get_request_for_application_success_view)
    assert response.context_data.get('submission_date') == user_application_hub.submission_date
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_user_without_submitted_application_for_application_success_view(logged_in_client):
    """
    Test the case where a user has not submitted their application.
    """
    response = logged_in_client.get(reverse('application_success'))
    assert response.status_code == 400


@pytest.mark.django_db
def test_get_no_user_application_exists_for_application_success_view(get_request_for_application_success_view):
    """
    Test the case where a user does not have an associated ApplicationHub object.
    """
    get_request_for_application_success_view.user.application_hub = None

    response = ApplicationSuccessView.as_view()(get_request_for_application_success_view)
    assert response.status_code == 400
