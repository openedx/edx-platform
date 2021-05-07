"""
All test cases for webinars app views
"""

import mock
import pytest
from django.urls import reverse

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.webinars.models import Webinar
from openedx.adg.lms.webinars.tests.factories import WebinarFactory

pytestmark = pytest.mark.django_db


@pytest.fixture(name='user_client')
def user_client_login(request, client):
    """
    User and client login fixture. User will be authenticated for all tests where we pass this fixture.
    """
    user = UserFactory()
    client.login(username=user.username, password='test')
    return user, client


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
    webinar = WebinarFactory(is_cancelled=False)

    client.get(reverse('webinar_event', kwargs={'pk': webinar.id}))

    mock_select_template.assert_called_once_with(
        ['adg/lms/webinar/description_page.html'], using=None
    )
