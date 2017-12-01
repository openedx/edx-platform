"""
Tests the execution of forum notification tasks.
"""
from datetime import datetime, timedelta
import json
import math

from crum import CurrentRequestUserMiddleware
import ddt
from django.contrib.sites.models import Site
import mock

import lms.lib.comment_client as cc

from django_comment_common.models import ForumsConfig
from django_comment_common.signals import comment_created
from edx_ace.recipient import Recipient
from edx_ace.renderers import EmailRenderer
from edx_ace.utils import date
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS, SEND_NOTIFICATIONS_FOR_COURSE
from lms.djangoapps.discussion.signals.handlers import ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY
from lms.djangoapps.discussion.tasks import _should_send_message
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.schedules.template_context import get_base_template_context
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.theming.middleware import CurrentSiteThemeMiddleware
from openedx.core.djangoapps.waffle_utils.testutils import override_waffle_flag
from openedx.core.lib.celery.task_utils import emulate_http_request
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


NOW = datetime.utcnow()
ONE_HOUR_AGO = NOW - timedelta(hours=1)
TWO_HOURS_AGO = NOW - timedelta(hours=2)


def make_mock_responder(subscribed_thread_ids=None, thread_data=None, comment_data=None, per_page=1):
    def mock_subscribed_threads(method, url, **kwargs):
        subscribed_thread_collection = [
            {'id': thread_id} for thread_id in subscribed_thread_ids
        ]
        page = kwargs.get('params', {}).get('page', 1)
        start_index = per_page * (page - 1)
        end_index = per_page * page
        data = {
            'collection': subscribed_thread_collection[start_index: end_index],
            'page': page,
            'num_pages': int(math.ceil(len(subscribed_thread_collection) / float(per_page))),
            'thread_count': len(subscribed_thread_collection)
        }
        return mock.Mock(status_code=200, text=json.dumps(data), json=mock.Mock(return_value=data))

    def mock_comment_find(method, url, **kwargs):
        return mock.Mock(status_code=200, text=json.dumps(comment_data), json=mock.Mock(return_value=comment_data))

    def mock_thread_find(method, url, **kwargs):
        return mock.Mock(status_code=200, text=json.dumps(thread_data), json=mock.Mock(return_value=thread_data))

    def mock_request(method, url, **kwargs):
        if '/subscribed_threads' in url:
            return mock_subscribed_threads(method, url, **kwargs)
        if '/comments' in url:
            return mock_comment_find(method, url, **kwargs)
        if '/threads' in url:
            return mock_thread_find(method, url, **kwargs)

    return mock_request


@ddt.ddt
class TaskTestCase(ModuleStoreTestCase):
    @classmethod
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUpClass(cls):
        super(TaskTestCase, cls).setUpClass()
        cls.discussion_id = 'dummy_discussion_id'
        cls.course = CourseOverviewFactory.create(language='fr')

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with mock.patch('student.models.cc.User.save'):
            cls.thread_author = UserFactory(
                username='thread_author',
                password='password',
                email='email'
            )
            cls.comment_author = UserFactory(
                username='comment_author',
                password='password',
                email='email'
            )

            CourseEnrollmentFactory(
                user=cls.thread_author,
                course_id=cls.course.id
            )
            CourseEnrollmentFactory(
                user=cls.comment_author,
                course_id=cls.course.id
            )

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

        cls.create_thread_and_comments()

    @classmethod
    def create_thread_and_comments(cls):
        cls.thread = {
            'id': cls.discussion_id,
            'course_id': unicode(cls.course.id),
            'created_at': date.serialize(TWO_HOURS_AGO),
            'title': 'thread-title',
            'user_id': cls.thread_author.id,
            'username': cls.thread_author.username,
            'commentable_id': 'thread-commentable-id',
        }
        cls.comment = {
            'id': 'comment',
            'body': 'comment-body',
            'created_at': date.serialize(ONE_HOUR_AGO),
            'thread_id': cls.thread['id'],
            'parent_id': None,
            'user_id': cls.comment_author.id,
            'username': cls.comment_author.username,
        }
        cls.comment2 = {
            'id': 'comment2',
            'body': 'comment2-body',
            'created_at': date.serialize(NOW),
            'thread_id': cls.thread['id'],
            'parent_id': None,
            'user_id': cls.comment_author.id,
            'username': cls.comment_author.username
        }
        cls.subcomment = {
            'id': 'subcomment',
            'body': 'subcomment-body',
            'created_at': date.serialize(NOW),
            'thread_id': cls.thread['id'],
            'parent_id': cls.comment['id'],
            'user_id': cls.comment_author.id,
            'username': cls.comment_author.username,
        }
        cls.thread['children'] = [cls.comment, cls.comment2]
        cls.comment['child_count'] = 1,

    def setUp(self):
        super(TaskTestCase, self).setUp()
        self.request_patcher = mock.patch('requests.request')
        self.mock_request = self.request_patcher.start()

        self.ace_send_patcher = mock.patch('edx_ace.ace.send')
        self.mock_ace_send = self.ace_send_patcher.start()

        thread_permalink = '/courses/discussion/dummy_discussion_id'
        self.permalink_patcher = mock.patch('lms.djangoapps.discussion.tasks.permalink', return_value=thread_permalink)
        self.mock_permalink = self.permalink_patcher.start()

    def tearDown(self):
        super(TaskTestCase, self).tearDown()
        self.request_patcher.stop()
        self.ace_send_patcher.stop()
        self.permalink_patcher.stop()

    @ddt.data(True, False)
    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def test_send_discussion_email_notification(self, user_subscribed):
        if user_subscribed:
            non_matching_id = 'not-a-match'
            # with per_page left with a default value of 1, this ensures
            # that we test a multiple page result when calling
            # comment_client.User.subscribed_threads()
            subscribed_thread_ids = [non_matching_id, self.discussion_id]
        else:
            subscribed_thread_ids = []

        self.mock_request.side_effect = make_mock_responder(
            subscribed_thread_ids=subscribed_thread_ids,
            comment_data=self.comment,
            thread_data=self.thread,
        )
        user = mock.Mock()
        comment = cc.Comment.find(id=self.comment['id']).retrieve()
        site = Site.objects.get_current()
        site_config = SiteConfigurationFactory.create(site=site)
        site_config.values[ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY] = True
        site_config.save()
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
            with mock.patch('lms.djangoapps.discussion.signals.handlers.get_current_site', return_value=site):
                comment_created.send(sender=None, user=user, post=comment)

        if user_subscribed:
            expected_message_context = get_base_template_context(site)
            expected_message_context.update({
                'comment_author_id': self.comment_author.id,
                'comment_body': self.comment['body'],
                'comment_created_at': ONE_HOUR_AGO,
                'comment_id': self.comment['id'],
                'comment_username': self.comment_author.username,
                'course_id': self.course.id,
                'thread_author_id': self.thread_author.id,
                'thread_created_at': TWO_HOURS_AGO,
                'thread_id': self.discussion_id,
                'thread_title': 'thread-title',
                'thread_username': self.thread_author.username,
                'thread_commentable_id': self.thread['commentable_id'],
                'post_link': self.mock_permalink.return_value,
                'site': site,
                'site_id': site.id
            })
            expected_recipient = Recipient(self.thread_author.username, self.thread_author.email)
            actual_message = self.mock_ace_send.call_args_list[0][0][0]
            self.assertEqual(expected_message_context, actual_message.context)
            self.assertEqual(expected_recipient, actual_message.recipient)
            self.assertEqual(self.course.language, actual_message.language)
            self._assert_rendered_email(actual_message)
        else:
            self.assertFalse(self.mock_ace_send.called)

    def _assert_rendered_email(self, message):
        # check that we can actually render the message
        with emulate_http_request(
            site=message.context['site'], user=self.thread_author
        ):
            rendered_email = EmailRenderer().render(message)
            self.assertTrue(self.comment['body'] in rendered_email.body_html)
            self.assertTrue(self.comment_author.username in rendered_email.body_html)
            self.assertTrue(self.thread_author.username in rendered_email.body_html)
            self.assertTrue(self.mock_permalink in rendered_email.body_html)
            self.assertTrue(message.context['site'].domain in rendered_email.body_html)

    @override_waffle_flag(SEND_NOTIFICATIONS_FOR_COURSE, True)
    def run_should_not_send_email_test(self, comment_dict):
        self.mock_request.side_effect = make_mock_responder(
            subscribed_thread_ids=[self.discussion_id],
            comment_data=comment_dict,
            thread_data=self.thread,
        )
        user = mock.Mock()
        comment = cc.Comment.find(id=comment_dict['id']).retrieve()
        with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
            comment_created.send(sender=None, user=user, post=comment)

        actual_result = _should_send_message({
            'thread_author_id': self.thread_author.id,
            'course_id': self.course.id,
            'comment_id': comment_dict['id'],
            'thread_id': self.thread['id'],
        })
        self.assertEqual(actual_result, False)
        self.assertFalse(self.mock_ace_send.called)

    def test_subcomment_should_not_send_email(self):
        self.run_should_not_send_email_test(self.subcomment)

    def test_second_comment_should_not_send_email(self):
        self.run_should_not_send_email_test(self.comment2)
