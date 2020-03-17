import ddt

from django.conf import settings
from django.test import TestCase
from mock import patch, ANY

from edx_ace.recipient import Recipient
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.features.ucsd_features.message_types import ContactSupportNotification, CommerceSupportNotification
from openedx.features.ucsd_features.utils import send_notification, send_notification_email_to_support


MESSAGE_TYPES = {
    'contact_support': ContactSupportNotification,
    'commerce_support': CommerceSupportNotification
}


@ddt.ddt
class UCSDFeaturesUtilsTests(ModuleStoreTestCase):
    """
    Tests for the utils used by ucsd-specific customizations
    """

    def setUp(self):
        super(UCSDFeaturesUtilsTests, self).setUp()
        self.test_emails = ['test@demo.com', ]
        self.course = CourseFactory.create()

    @ddt.data(*MESSAGE_TYPES)
    @patch('openedx.features.ucsd_features.utils.ace.send')
    def test_send_notification_method_success(self, message_type, mocked_send):
        """
        Test the send_notification method success flow
        """
        with patch.object(MESSAGE_TYPES[message_type], 'personalize') as mocked_personalize:
            test_recipient = Recipient(username='', email_address=self.test_emails[0])
            returned_value = send_notification(message_type, {}, self.test_emails)

            mocked_send.assertCalled()
            self.assertTrue(returned_value)
            mocked_personalize.assert_called_with(user_context=ANY, recipient=test_recipient, language='en')

    @ddt.data(*MESSAGE_TYPES)
    @patch('openedx.features.ucsd_features.utils.ace.send', side_effect=Exception)
    def test_send_notification_method_failure(self, message_type, mocked_send):
        """
        Test the send_notification method failure flow. In case of any exception,
        that exception is handled and `False` is returned.
        """
        returned_value = send_notification(message_type, {}, self.test_emails)

        mocked_send.assertCalled()
        self.assertFalse(returned_value)

    @patch('openedx.features.ucsd_features.utils.send_notification', return_value=True)
    def test_send_notification_email_to_support_method(self, mocked_send_notification):
        """
        Test the send_notification_email_to_support method and verify that `send_notification` method
        is called with correct parameters.
        """
        test_course_key = unicode(self.course.id)
        dest_emails = settings.SUPPORT_DESK_EMAILS
        test_data = {
            'subject': 'test_subject',
            'name': 'test_name',
            'email': 'test_email',
            'body': 'test_body',
            'custom_fields': [
                {'value': test_course_key}
            ]
        }

        response = send_notification_email_to_support(message_type='contact_support', **test_data)
        mocked_send_notification.assert_called_with('contact_support', ANY, dest_emails)
        self.assertTrue(response)
