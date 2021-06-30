"""
Test classes for the events sent in the registration process.

Classes:
    RegistrationEventTest: Test event sent after registering a user through the
    user API.
    LoginSessionEventTest: Test event sent after creating the user's login session
    user through the user API.
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.urls import reverse
from mock import patch
from openedx_events.learning.data import UserData, UserPersonalData

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.core.djangoapps.user_api.tests.test_views import UserAPITestCase
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class RegistrationEventTest(UserAPITestCase):
    """
    Tests for the Open edX Events associated with the registration process through
    the user API.

    This class guarantees that the following events are sent after registering
    a user, with the exact Data Attributes as the event definition stated:

        - STUDENT_REGISTRATION_COMPLETED: after the user's registration has been
        completed.
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.url = reverse("user_api_registration")
        self.user_info = {
            "email": "user@example.com",
            "name": "Test User",
            "username": "test",
            "password": "password",
            "honor_code": "true",
        }

    @patch("openedx.core.djangoapps.user_authn.views.register.STUDENT_REGISTRATION_COMPLETED")
    def test_send_registration_event(self, registration_event):
        """
        Test whether the student registration event is sent during the user's
        registration process.

        Expected result:
            - STUDENT_REGISTRATION_COMPLETED is sent via send_event.
            - The arguments match the event definition.
        """
        self.client.post(self.url, self.user_info)

        user = User.objects.get(username=self.user_info.get("username"))
        registration_event.send_event.assert_called_once_with(
            user=UserData(
                pii=UserPersonalData(
                    username=user.username,
                    email=user.email,
                    name=user.profile.name,
                ),
                id=user.id,
                is_active=user.is_active,
            ),
        )


@skip_unless_lms
class LoginSessionEventTest(UserAPITestCase):
    """
    Tests for the Open edX Events associated with the login process through the
    user API.

    This class guarantees that the following events are sent after the user's
    session creation, with the exact Data Attributes as the event definition
    stated:

        - SESSION_LOGIN_COMPLETED: after login has been completed.
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.url = reverse("user_api_login_session", kwargs={"api_version": "v1"})
        self.user = UserFactory.create(
            username="test",
            email="test@example.com",
            password="password",
        )
        self.user_profile = UserProfileFactory.create(user=self.user, name="Test Example")

    @patch("openedx.core.djangoapps.user_authn.views.login.SESSION_LOGIN_COMPLETED")
    def test_send_login_event(self, login_event):
        """
        Test whether the student login event is sent after the user's
        login process.

        Expected result:
            - SESSION_LOGIN_COMPLETED is sent via send_event.
            - The arguments match the event definition.
        """
        data = {
            "email": "test@example.com",
            "password": "password",
        }

        self.client.post(self.url, data)

        login_event.send_event.assert_called_once_with(
            user=UserData(
                pii=UserPersonalData(
                    username=self.user.username,
                    email=self.user.email,
                    name=self.user.profile.name,
                ),
                id=self.user.id,
                is_active=self.user.is_active,
            ),
        )
