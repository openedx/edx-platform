"""
Unit tests for badging tasks
"""
import mock
from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from common.lib.mandrill_client.client import MandrillClient
from student.tests.factories import UserFactory

from .. import tasks as badging_tasks
from ..constants import COURSE_ID_KEY, MY_BADGES_URL_NAME


class BadgeViewsTestCases(TestCase):

    @mock.patch('openedx.features.badging.helpers.notifications.send_user_badge_notification')
    @mock.patch('openedx.features.badging.tasks.MandrillClient.send_mail')
    def test_task_user_badge_notify_successfully(self, mock_send_mail, mock_send_user_badge_notification):
        """
        Test for notifying user that he has earned new badges by asserting data params of relevant functions from
        mandrill client and badge handler
        """
        user = UserFactory()
        context = {
            'my_badge_url': u'{host}{path}'.format(
                host=settings.LMS_ROOT_URL,
                path=reverse(MY_BADGES_URL_NAME, kwargs={COURSE_ID_KEY: 'abc/123/xyz'})
            )
        }

        badging_tasks.task_user_badge_notify(user, 'abc/123/xyz', 'team')

        mock_send_mail.assert_called_once_with(MandrillClient.USER_BADGE_EMAIL_TEMPLATE, user.email, context)
        mock_send_user_badge_notification.assert_called_once_with(user, mock.ANY, 'team')
