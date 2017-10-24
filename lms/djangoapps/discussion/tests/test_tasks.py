import ddt
from django.test.client import Client
from mock import patch
from nose.tools import assert_true

from edx_ace.recipient import Recipient
from lms.djangoapps.discussion.tasks import send_ace_message, ResponseNotification
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from django_comment_common.models import (
    CourseDiscussionSettings,
    ForumsConfig,
    FORUM_ROLE_STUDENT,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class BlaTestCase(ModuleStoreTestCase):

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(BlaTestCase, self).setUp()

    # Sofiya - we probably don't need all these objects
        self.course = CourseFactory.create(discussion_topics={'dummy discussion': {'id': 'dummy_discussion_id'}})
        self.thread_user = UserFactory(
            username='thread_user',
            password='password',
            email='email'
        )
        self.comment_user = UserFactory(
            username='comment_user',
            password='password',
            email='email'
        )

        CourseEnrollmentFactory(
            user=self.thread_user,
            course_id=self.course.id
        )
        CourseEnrollmentFactory(
            user=self.comment_user,
            course_id=self.course.id
        )

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            uname = 'student'
            email = 'student@edx.org'
            password = 'test'

            # Create the student
            self.student = UserFactory(username=uname, password=password, email=email)

            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            assert_true(self.client.login(username=uname, password=password))

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    # Sofiya - building the whole message seems like overkill, we just want the context
    def _create_sample_response_notification(self):
        message = ResponseNotification().personalize(
            Recipient(self.comment_user.username, self.comment_user.email),
            _get_course_language(course_id),
            context
        )
        return message

    # Sofiya - create new method to check that ace send message was called correctly, and call that in all the tests

    # Sofiya - figure out what needs to be mocked and what doesn't
    @ddt.data(True, False)
    def test_send_message(self, mock_from_django_user, is_user_subscribed):
        with patch('student.models.cc.User.subscribed_threads', return_value=is_user_subscribed) and patch('edx_ace.send') as ace_message:
            send_ace_message(
                thread_id='dummy_discussion_id',
                thread_user_id=self.thread_user.id,
                comment_user_id=self.comment_user.id,
                course_id=self.course.id
            )
            # Sofiya - check context of the message to make sure it is called with the right thing
            if is_user_subscribed:
                self.assertTrue(ace_message.called)
            else:
                self.assertFalse(ace_message.called)

