"""
Unit tests for bulk-email-related models with EOL Customizations.
"""

from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey

from bulk_email.models import (
    SEND_TO_STAFF,
    CourseEmail,
)
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class EOLCourseEmailTest(ModuleStoreTestCase):
    """Test the CourseEmail model using reply_to customization."""

    def test_creation_with_reply_to(self):
        course_id = CourseKey.from_string('abc/123/doremieol')
        sender = UserFactory.create()
        to_option = SEND_TO_STAFF
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        reply_to = "dummy@email.dummy"
        email = CourseEmail.create(course_id, sender, [to_option], subject, html_message, reply_to=reply_to)
        self.assertEqual(email.course_id, course_id)
        self.assertIn(SEND_TO_STAFF, [target.target_type for target in email.targets.all()])
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.html_message, html_message)
        self.assertEqual(email.sender, sender)
        self.assertEqual(email.reply_to, reply_to)