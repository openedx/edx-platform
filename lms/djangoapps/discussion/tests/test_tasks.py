"""
Tests the execution of forum notification tasks.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta
import json
import math
from urlparse import urljoin

import ddt
from django.conf import settings
from django.contrib.sites.models import Site
import mock

from django_comment_common.models import ForumsConfig
from django_comment_common.signals import comment_created
from edx_ace.recipient import Recipient
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS
from lms.djangoapps.discussion.tasks import _generate_ga_pixel_url
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.schedules.template_context import get_base_template_context
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@contextmanager
def mock_the_things():
    thread_permalink = '/courses/discussion/dummy_discussion_id'
    with mock.patch('requests.request') as mock_request, mock.patch('edx_ace.ace.send') as mock_ace_send:
        with mock.patch('lms.djangoapps.discussion.tasks.permalink', return_value=thread_permalink) as mock_permalink:
            with mock.patch('lms.djangoapps.discussion.tasks.cc.Thread'):
                yield (mock_request, mock_ace_send, mock_permalink)


def make_mock_responder(thread_ids, per_page=1):
    collection = [
        {'id': thread_id} for thread_id in thread_ids
    ]

    def mock_response(*args, **kwargs):
        page = kwargs.get('params', {}).get('page', 1)
        start_index = per_page * (page - 1)
        end_index = per_page * page
        data = {
            'collection': collection[start_index: end_index],
            'page': page,
            'num_pages': int(math.ceil(len(collection) / float(per_page))),
            'thread_count': len(collection)
        }
        return mock.Mock(status_code=200, text=json.dumps(data), json=mock.Mock(return_value=data))
    return mock_response


@ddt.ddt
class TaskTestCase(ModuleStoreTestCase):

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super(TaskTestCase, self).setUp()

        self.discussion_id = 'dummy_discussion_id'
        self.course = CourseOverviewFactory.create(language='fr')

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with mock.patch('student.models.cc.User.save'):

            self.thread_author = UserFactory(
                username='thread_author',
                password='password',
                email='email'
            )
            self.comment_author = UserFactory(
                username='comment_author',
                password='password',
                email='email'
            )

            CourseEnrollmentFactory(
                user=self.thread_author,
                course_id=self.course.id
            )
            CourseEnrollmentFactory(
                user=self.comment_author,
                course_id=self.course.id
            )

        config = ForumsConfig.current()
        config.enabled = True
        config.save()

    @ddt.data(True, False)
    def test_send_discussion_email_notification(self, user_subscribed):
        with mock_the_things() as mocked_items:
            mock_request, mock_ace_send, mock_permalink = mocked_items
            if user_subscribed:
                non_matching_id = 'not-a-match'
                # with per_page left with a default value of 1, this ensures
                # that we test a multiple page result when calling
                # comment_client.User.subscribed_threads()
                mock_request.side_effect = make_mock_responder([non_matching_id, self.discussion_id])
            else:
                mock_request.side_effect = make_mock_responder([])

            now = datetime.utcnow()
            one_hour_ago = now - timedelta(hours=1)
            thread = mock.Mock(
                id=self.discussion_id,
                course_id=self.course.id,
                created_at=one_hour_ago,
                title='thread-title',
                user_id=self.thread_author.id,
                username=self.thread_author.username,
                commentable_id='thread-commentable-id'
            )
            comment = mock.Mock(
                id='comment-id',
                body='comment-body',
                created_at=now,
                thread=thread,
                user_id=self.comment_author.id,
                username=self.comment_author.username
            )
            user = mock.Mock()

            with waffle().override(FORUM_RESPONSE_NOTIFICATIONS):
                comment_created.send(sender=None, user=user, post=comment)

            if user_subscribed:
                expected_message_context = get_base_template_context(Site.objects.get_current())
                expected_message_context.update({
                    'comment_author_id': self.comment_author.id,
                    'comment_body': 'comment-body',
                    'comment_created_at': now,
                    'comment_id': 'comment-id',
                    'comment_username': self.comment_author.username,
                    'course_id': self.course.id,
                    'thread_author_id': self.thread_author.id,
                    'thread_created_at': one_hour_ago,
                    'thread_id': self.discussion_id,
                    'thread_title': 'thread-title',
                    'thread_username': self.thread_author.username,
                    'thread_commentable_id': 'thread-commentable-id',
                    'post_link': urljoin(Site.objects.get_current().domain, mock_permalink.return_value),
                    'site': Site.objects.get_current(),
                    'site_id': Site.objects.get_current().id,
                })
                ga_tracking_pixel_url = _generate_ga_pixel_url(expected_message_context)
                expected_message_context.update({'ga_tracking_pixel_url': ga_tracking_pixel_url})
                expected_recipient = Recipient(self.thread_author.username, self.thread_author.email)
                actual_message = mock_ace_send.call_args_list[0][0][0]
                self.assertEqual(expected_message_context, actual_message.context)
                self.assertEqual(expected_recipient, actual_message.recipient)
                self.assertEqual(self.course.language, actual_message.language)
            else:
                self.assertFalse(mock_ace_send.called)
