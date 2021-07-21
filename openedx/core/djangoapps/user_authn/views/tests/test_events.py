"""
Test classes for the events sent in the registration process.

Classes:
    RegistrationEventTest: Test event sent while registering a user through the user API.
"""
from django.contrib.auth.models import User
from django.urls import reverse
from mock import patch
from openedx_events.learning.data import UserData, UserNonPersonalData, UserPersonalData

from openedx.core.djangoapps.user_api.tests.test_views import UserAPITestCase
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class RegistrationEventTest(UserAPITestCase):
    """
    Tests for the events associated with the registration process through the user API.

    This class guarantees that STUDENT_REGISTRATION_COMPLETED event is sent while registering
    a user, with the exact Data Attributes as the event definition stated.
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
                user_non_pii=UserNonPersonalData(
                    id=user.id,
                    is_active=user.is_active,
                ),
                user=UserPersonalData(
                    username=user.username,
                    email=user.email,
                    name=user.profile.name,
                )
            ),
        )
