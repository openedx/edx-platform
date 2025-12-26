"""
Tests for discussion moderation tasks.
"""
from unittest import mock
from django.test import override_settings

from lms.djangoapps.discussion.rest_api.tasks import delete_course_post_for_user
from forum.backends.mysql.models import DiscussionBan, ModerationAuditLog
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class DeleteCoursePostForUserTaskTest(ModuleStoreTestCase):
    """Tests for delete_course_post_for_user Celery task."""

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(org='TestX', number='CS101', run='2024')
        self.course_key = str(self.course.id)
        self.user = UserFactory.create()
        self.moderator = UserFactory.create()

    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    def test_delete_posts_without_ban(self, mock_segment, mock_tracker,
                                      mock_delete_threads, mock_delete_comments):
        """Test deleting posts without banning the user."""
        # Mock forum service responses
        mock_delete_threads.return_value = 2
        mock_delete_comments.return_value = 3

        # Execute task
        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'username': self.user.username,
            'course_ids': [self.course_key],
            'ban_user': False
        }).get()

        # Verify deletions were called
        mock_delete_threads.assert_called_once_with(self.user.id, [self.course_key])
        mock_delete_comments.assert_called_once_with(self.user.id, [self.course_key])

        # Verify no ban was created
        self.assertFalse(DiscussionBan.objects.filter(user=self.user).exists())

        # Verify result
        self.assertEqual(result['threads_deleted'], 2)
        self.assertEqual(result['comments_deleted'], 3)
        self.assertFalse(result['ban_applied'])

    @override_settings(DISCUSSION_MODERATION_BAN_EMAIL_ENABLED=True)
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    @mock.patch('lms.djangoapps.discussion.rest_api.emails.send_ban_escalation_email')
    def test_delete_posts_with_course_ban(self, mock_send_email, mock_segment,
                                          mock_tracker, mock_delete_threads,
                                          mock_delete_comments):
        """Test deleting posts with course-level ban."""
        # Mock forum service responses
        mock_delete_threads.return_value = 1
        mock_delete_comments.return_value = 2

        # Execute task with ban
        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'username': self.user.username,
            'course_ids': [self.course_key],
            'ban_user': True,
            'ban_scope': 'course',
            'moderator_id': self.moderator.id,
            'reason': 'Posting spam'
        }).get()

        # Verify ban was created
        ban = DiscussionBan.objects.get(user=self.user, course_id=self.course_key)
        self.assertTrue(ban.is_active)
        self.assertEqual(ban.scope, 'course')
        self.assertEqual(ban.reason, 'Posting spam')

        # Verify moderation log was created
        log = ModerationAuditLog.objects.get(target_user=self.user)
        self.assertEqual(log.action_type, 'ban_user')
        self.assertEqual(log.source, ModerationAuditLog.SOURCE_HUMAN)
        self.assertEqual(log.moderator, self.moderator)
        self.assertIsNotNone(log.metadata)
        if log.metadata:
            self.assertEqual(log.metadata.get('threads_deleted'), 1)
            self.assertEqual(log.metadata.get('comments_deleted'), 2)

        # Verify email was sent
        mock_send_email.assert_called_once()

        # Verify result includes ban info
        self.assertTrue(result['ban_applied'])

    @override_settings(DISCUSSION_MODERATION_BAN_EMAIL_ENABLED=True)
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    @mock.patch('lms.djangoapps.discussion.rest_api.emails.send_ban_escalation_email')
    def test_delete_posts_with_org_ban(self, mock_send_email, mock_segment,
                                       mock_tracker, mock_delete_threads,
                                       mock_delete_comments):
        """Test deleting posts with organization-level ban."""
        mock_delete_threads.return_value = 5
        mock_delete_comments.return_value = 10

        # Execute task with org-level ban
        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'username': self.user.username,
            'course_ids': [self.course_key],
            'ban_user': True,
            'ban_scope': 'organization',
            'moderator_id': self.moderator.id,
            'reason': 'Multiple violations'
        }).get()

        # Verify org-level ban was created
        ban = DiscussionBan.objects.get(user=self.user, org_key='TestX')
        self.assertEqual(ban.scope, 'organization')
        self.assertIsNone(ban.course_id)

        # Verify result
        self.assertTrue(result['ban_applied'])
        self.assertEqual(result['threads_deleted'], 5)

    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    def test_no_posts_to_delete(self, mock_segment, mock_tracker,
                                mock_delete_threads, mock_delete_comments):
        """Test task when user has no posts."""
        mock_delete_threads.return_value = 0
        mock_delete_comments.return_value = 0

        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'course_ids': [self.course_key],
            'ban_user': False
        }).get()

        self.assertEqual(result['threads_deleted'], 0)
        self.assertEqual(result['comments_deleted'], 0)

    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    def test_task_handles_failure(self, mock_delete_threads, mock_delete_comments):
        """Test that task raises exception on failure."""
        # Simulate forum service error
        mock_delete_threads.side_effect = Exception("Forum service error")

        with self.assertRaises(Exception):
            delete_course_post_for_user.apply(kwargs={
                'user_id': self.user.id,
                'course_ids': [self.course_key],
                'ban_user': False
            }).get()

    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    def test_backward_compatibility_without_ban_param(self, mock_segment, mock_tracker,
                                                      mock_delete_threads,
                                                      mock_delete_comments):
        """Test that task works without ban_user parameter (backward compatibility)."""
        mock_delete_threads.return_value = 1
        mock_delete_comments.return_value = 0

        # Call without ban_user parameter (defaults to False)
        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'course_ids': [self.course_key]
        }).get()

        # Should work and not ban user
        self.assertFalse(DiscussionBan.objects.filter(user=self.user).exists())
        self.assertEqual(result['threads_deleted'], 1)
        self.assertFalse(result['ban_applied'])

    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    @mock.patch('lms.djangoapps.discussion.rest_api.emails.send_ban_escalation_email')
    def test_email_failure_doesnt_break_task(self, mock_send_email, mock_segment,
                                             mock_tracker, mock_delete_threads,
                                             mock_delete_comments):
        """Test that email send failure doesn't break the task."""
        mock_delete_threads.return_value = 1
        mock_delete_comments.return_value = 1
        mock_send_email.side_effect = Exception("SMTP error")

        # Task should complete despite email failure
        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'course_ids': [self.course_key],
            'ban_user': True,
            'moderator_id': self.moderator.id,
            'reason': 'Test'
        }).get()

        # Ban should still be created
        self.assertTrue(DiscussionBan.objects.filter(user=self.user).exists())
        self.assertTrue(result['ban_applied'])

    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    def test_reactivates_inactive_ban(self, mock_segment, mock_tracker,
                                      mock_delete_threads, mock_delete_comments):
        """Test that an inactive ban is reactivated."""
        # Create an inactive ban
        inactive_ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Old ban',
            is_active=False
        )

        mock_delete_threads.return_value = 1
        mock_delete_comments.return_value = 0

        # Re-ban the user
        delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'course_ids': [self.course_key],
            'ban_user': True,
            'moderator_id': self.moderator.id,
            'reason': 'New ban'
        }).get()

        # Ban should be reactivated
        inactive_ban.refresh_from_db()
        self.assertTrue(inactive_ban.is_active)
        self.assertEqual(inactive_ban.reason, 'New ban')

    @override_settings(DISCUSSION_MODERATION_BAN_EMAIL_ENABLED=False)
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    @mock.patch('lms.djangoapps.discussion.rest_api.emails.send_ban_escalation_email')
    def test_email_not_sent_when_disabled(self, mock_send_email, mock_segment,
                                          mock_tracker, mock_delete_threads,
                                          mock_delete_comments):
        """Test that email is not sent when DISCUSSION_MODERATION_BAN_EMAIL_ENABLED is False."""
        mock_delete_threads.return_value = 1
        mock_delete_comments.return_value = 1

        # Execute task with ban
        delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'username': self.user.username,
            'course_ids': [self.course_key],
            'ban_user': True,
            'ban_scope': 'course',
            'moderator_id': self.moderator.id,
            'reason': 'Spam'
        }).get()

        # Ban should be created
        self.assertTrue(DiscussionBan.objects.filter(user=self.user).exists())

        # Email should NOT be sent when setting is False
        mock_send_email.assert_not_called()

    @override_settings(
        DISCUSSION_MODERATION_BAN_EMAIL_ENABLED=True,
        DISCUSSION_MODERATION_ESCALATION_EMAIL='custom-support@example.com'
    )
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.Comment.delete_user_comments')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.thread.Thread.delete_user_threads')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.tracker.emit')
    @mock.patch('lms.djangoapps.discussion.rest_api.tasks.segment.track')
    @mock.patch('lms.djangoapps.discussion.rest_api.emails.send_ban_escalation_email')
    def test_email_sent_to_custom_address(self, mock_send_email, mock_segment,
                                          mock_tracker, mock_delete_threads,
                                          mock_delete_comments):
        """Test that email respects custom escalation email setting."""
        mock_delete_threads.return_value = 2
        mock_delete_comments.return_value = 3

        # Execute task with ban
        result = delete_course_post_for_user.apply(kwargs={
            'user_id': self.user.id,
            'username': self.user.username,
            'course_ids': [self.course_key],
            'ban_user': True,
            'ban_scope': 'course',
            'moderator_id': self.moderator.id,
            'reason': 'Policy violation'
        }).get()

        # Email should be called with correct parameters
        mock_send_email.assert_called_once_with(
            banned_user_id=self.user.id,
            moderator_id=self.moderator.id,
            course_id=self.course_key,
            scope='course',
            reason='Policy violation',
            threads_deleted=2,
            comments_deleted=3,
        )

        # Verify result includes ban info
        self.assertTrue(result['ban_applied'])
        self.assertEqual(result['threads_deleted'], 2)
        self.assertEqual(result['comments_deleted'], 3)
