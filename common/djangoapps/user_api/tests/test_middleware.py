"""Tests for user API middleware"""
from mock import Mock, patch
from unittest import TestCase

from django.http import HttpResponse
from django.test.client import RequestFactory

from student.tests.factories import UserFactory, AnonymousUserFactory
from user_api.tests.factories import UserCourseTagFactory
from user_api.middleware import UserTagsEventContextMiddleware


class TagsMiddlewareTest(TestCase):
    """
    Test the UserTagsEventContextMiddleware
    """
    def setUp(self):
        self.middleware = UserTagsEventContextMiddleware()
        self.user = UserFactory.create()
        self.other_user = UserFactory.create()

        self.course_id = 'mock/course/id'
        self.request_factory = RequestFactory()

        # TODO: Make it so we can use reverse. Appears to fail depending on the order in which tests are run
        #self.request = RequestFactory().get(reverse('courseware', kwargs={'course_id': self.course_id}))
        self.request = RequestFactory().get('/courses/{}/courseware'.format(self.course_id))
        self.request.user = self.user

        self.response = Mock(spec=HttpResponse)

        patcher = patch('user_api.middleware.tracker')
        self.tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def process_request(self):
        """
        Execute process request using the request, and verify that it returns None
        so that the request continues.
        """
        # Middleware should pass request through
        self.assertEquals(self.middleware.process_request(self.request), None)

    def assertContextSetTo(self, context):
        """Asserts UserTagsEventContextMiddleware.CONTEXT_NAME matches ``context``"""
        self.tracker.get_tracker.return_value.enter_context.assert_called_with(  # pylint: disable=maybe-no-member
            UserTagsEventContextMiddleware.CONTEXT_NAME,
            context
        )

    def test_tag_context(self):
        for key, value in (('int_value', 1), ('str_value', "two")):
            UserCourseTagFactory.create(
                course_id=self.course_id,
                user=self.user,
                key=key,
                value=value,
            )

        UserCourseTagFactory.create(
            course_id=self.course_id,
            user=self.other_user,
            key="other_user",
            value="other_user_value"
        )

        UserCourseTagFactory.create(
            course_id='other/course/id',
            user=self.user,
            key="other_course",
            value="other_course_value"
        )

        self.process_request()
        self.assertContextSetTo({
            'course_id': self.course_id,
            'course_user_tags': {
                'int_value': '1',
                'str_value': 'two',
            }
        })

    def test_no_tags(self):
        self.process_request()
        self.assertContextSetTo({'course_id': self.course_id, 'course_user_tags': {}})

    def test_not_course_url(self):
        self.request = self.request_factory.get('/not/a/course/url')
        self.request.user = self.user

        self.process_request()

        self.assertContextSetTo({})

    def test_invalid_course_id(self):
        self.request = self.request_factory.get('/courses/edX/101/')
        self.request.user = self.user

        self.process_request()
        self.assertContextSetTo({})

    def test_anonymous_user(self):
        self.request.user = AnonymousUserFactory()

        self.process_request()

        self.assertContextSetTo({'course_id': self.course_id, 'course_user_tags': {}})

    def test_remove_context(self):
        get_tracker = self.tracker.get_tracker  # pylint: disable=maybe-no-member
        exit_context = get_tracker.return_value.exit_context

        # The middleware should clean up the context when the request is done
        self.assertEquals(
            self.middleware.process_response(self.request, self.response),
            self.response
        )
        exit_context.assert_called_with(UserTagsEventContextMiddleware.CONTEXT_NAME)
        exit_context.reset_mock()

        # Even if the tracker blows up, the middleware should still return the response
        get_tracker.side_effect = Exception
        self.assertEquals(
            self.middleware.process_response(self.request, self.response),
            self.response
        )
