"""
Tests for discussion moderation views.

INTEGRATION TESTS - Requires MongoDB and full infrastructure.
These tests use ModuleStoreTestCase to create real courses in MongoDB and test
the full integration of the moderation views with course data, enrollments, and permissions.

Note: These tests are slower (~60s per test when MongoDB is not available) but provide
comprehensive integration testing. For faster unit tests, see test_moderation_views_v2.py.
"""

from unittest import mock
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from forum.backends.mysql.models import DiscussionBan, DiscussionModerationLog
from lms.djangoapps.discussion.toggles import ENABLE_DISCUSSION_BAN
from common.djangoapps.student.roles import CourseStaffRole, CourseInstructorRole
from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

User = get_user_model()


@mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
class DiscussionModerationViewSetTest(UrlResetMixin, ModuleStoreTestCase):
    """Integration tests for DiscussionModerationViewSet."""

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Create course with MongoDB (integration test)
        self.course = CourseFactory.create(
            org='TestX',
            course='CS101',
            run='2024'
        )
        self.course_key = self.course.id

        # Create users
        self.student = UserFactory.create(username='student')
        self.moderator = UserFactory.create(username='moderator')
        self.admin = UserFactory.create(username='admin', is_staff=True)

        # Create enrollments
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course_key)
        CourseEnrollmentFactory.create(user=self.moderator, course_id=self.course_key)

        # Add moderator to course staff role
        CourseStaffRole(self.course_key).add_users(self.moderator)

    def test_bulk_delete_ban_permission_denied_for_student(self):
        """Test that students cannot access bulk delete/ban endpoint."""
        self.client.force_authenticate(user=self.student)

        url = reverse('discussion-moderation-bulk-delete-ban')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'ban_user': False
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @mock.patch('lms.djangoapps.discussion.rest_api.views.delete_course_post_for_user.apply_async')
    def test_bulk_delete_without_ban(self, mock_task):
        """Test bulk delete without banning the user."""
        # Mock the task to return a task-like object with an ID
        expected_task_id = 'test-task-id-123'
        mock_task.return_value = mock.Mock(id=expected_task_id)

        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-bulk-delete-ban')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'ban_user': False
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['task_id'], expected_task_id)

        # Verify task was called with correct kwargs
        mock_task.assert_called_once_with(
            kwargs={
                'user_id': self.student.id,
                'username': self.student.username,
                'course_ids': [str(self.course_key)],
                'ban_user': False,
                'ban_scope': 'course',
                'moderator_id': self.moderator.id,
                'reason': '',
            }
        )

        # Verify no ban was created
        self.assertFalse(DiscussionBan.objects.filter(user=self.student).exists())

    @mock.patch('lms.djangoapps.discussion.rest_api.views.delete_course_post_for_user.apply_async')
    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_bulk_delete_with_course_ban(self, mock_waffle, mock_task):
        """Test bulk delete with course-level ban."""
        # Mock task return value
        expected_task_id = 'task-id-456'
        mock_task.return_value = mock.Mock(id=expected_task_id)

        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-bulk-delete-ban')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'ban_user': True,
            'ban_scope': 'course',
            'reason': 'Posting spam content'
        }

        response = self.client.post(url, data, format='json')

        # Endpoint returns 202 Accepted for async operations
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('message', response.data)
        self.assertEqual(response.data['task_id'], expected_task_id)

        # Verify task was called with correct kwargs
        mock_task.assert_called_once_with(
            kwargs={
                'user_id': self.student.id,
                'username': self.student.username,
                'course_ids': [str(self.course_key)],
                'ban_user': True,
                'ban_scope': 'course',
                'moderator_id': self.moderator.id,
                'reason': 'Posting spam content',
            }
        )

        # Note: Ban and moderation log are created by the Celery task, not by the view
        # Those should be tested in test_moderation_tasks.py

    @mock.patch('lms.djangoapps.discussion.rest_api.views.delete_course_post_for_user.apply_async')
    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_bulk_delete_with_org_ban(self, mock_waffle, mock_task):
        """Test bulk delete with organization-level ban."""
        mock_task.return_value = mock.Mock(id='org-ban-task-id')

        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-bulk-delete-ban')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'ban_user': True,
            'ban_scope': 'organization',
            'reason': 'Multiple violations across courses'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        # Verify task was called with org scope
        mock_task.assert_called_once()
        call_kwargs = mock_task.call_args[1]['kwargs']
        self.assertEqual(call_kwargs['ban_scope'], 'organization')

        # Note: Ban is created by the Celery task, not by the view

    def test_bulk_delete_invalid_data(self):
        """Test bulk delete with invalid data returns 400."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-bulk-delete-ban')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'ban_user': True,
            'ban_scope': 'course'
            # Missing required 'reason' field
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('reason', response.data)

    def test_banned_users_list(self):
        """Test listing banned users for a course."""
        # Create some bans
        DiscussionBan.objects.create(
            user=self.student,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Test ban',
            is_active=True
        )

        other_user = UserFactory.create()
        DiscussionBan.objects.create(
            user=other_user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Another ban',
            is_active=True
        )

        # Inactive ban (should not appear)
        inactive_user = UserFactory.create()
        DiscussionBan.objects.create(
            user=inactive_user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Inactive',
            is_active=False
        )

        self.client.force_authenticate(user=self.moderator)
        url = reverse('discussion-moderation-banned-users', kwargs={'course_id': str(self.course_key)})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)

        usernames = [ban['username'] for ban in response.data['results']]
        self.assertIn('student', usernames)
        self.assertIn(other_user.username, usernames)
        self.assertNotIn(inactive_user.username, usernames)

    def test_banned_users_includes_org_bans(self):
        """Test that banned users list includes organization-level bans."""
        # Create org-level ban
        DiscussionBan.objects.create(
            user=self.student,
            org_key='TestX',
            scope='organization',
            banned_by=self.admin,
            reason='Org ban',
            is_active=True
        )

        self.client.force_authenticate(user=self.moderator)
        url = reverse('discussion-moderation-banned-users', kwargs={'course_id': str(self.course_key)})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['scope'], 'organization')

    def test_unban_user_course_level(self):
        """Test unbanning a user from a course."""
        ban = DiscussionBan.objects.create(
            user=self.student,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Test ban',
            is_active=True
        )

        self.client.force_authenticate(user=self.moderator)
        url = reverse('discussion-moderation-unban-user', kwargs={'pk': ban.id})
        data = {
            'user_id': self.student.id,
            'reason': 'Ban appeal approved'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify ban was deactivated
        ban.refresh_from_db()
        self.assertFalse(ban.is_active)
        self.assertIsNotNone(ban.unbanned_at)

        # Verify moderation log
        log = DiscussionModerationLog.objects.filter(
            target_user=self.student,
            action_type='unban_user'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.moderator, self.moderator)

    def test_unban_user_org_level_creates_exception(self):
        """Test unbanning from org-level ban creates an exception."""
        org_ban = DiscussionBan.objects.create(
            user=self.student,
            org_key='TestX',
            scope='organization',
            banned_by=self.admin,
            reason='Org ban',
            is_active=True
        )

        self.client.force_authenticate(user=self.moderator)
        url = reverse('discussion-moderation-unban-user', kwargs={'pk': org_ban.id})
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'reason': 'Exception for this course'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Org ban should still be active
        org_ban.refresh_from_db()
        self.assertTrue(org_ban.is_active)

        # Exception should exist
        from forum.backends.mysql.models import DiscussionBanException
        exception = DiscussionBanException.objects.filter(
            ban=org_ban,
            course_id=self.course_key
        ).first()
        self.assertIsNotNone(exception)

    def test_unban_user_not_banned(self):
        """Test unbanning a user who is not banned."""
        self.client.force_authenticate(user=self.moderator)
        # Use a non-existent ban ID
        url = reverse('discussion-moderation-unban-user', kwargs={'pk': 99999})
        data = {
            'user_id': self.student.id,
            'reason': 'Trying to unban'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unban_user_missing_reason(self):
        """Test that reason is required for unbanning."""
        ban = DiscussionBan.objects.create(
            user=self.student,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Test ban',
            is_active=True
        )

        self.client.force_authenticate(user=self.moderator)
        url = reverse('discussion-moderation-unban-user', kwargs={'pk': ban.id})
        data = {
            'user_id': self.student.id
            # Missing 'reason'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_permission_course_staff(self):
        """Test that course staff can access moderation endpoints."""
        staff_user = UserFactory.create()
        CourseStaffRole(self.course_key).add_users(staff_user)

        self.client.force_authenticate(user=staff_user)
        url = reverse('discussion-moderation-banned-users', kwargs={'course_id': str(self.course_key)})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permission_course_instructor(self):
        """Test that course instructors can access moderation endpoints."""
        instructor = UserFactory.create()
        CourseInstructorRole(self.course_key).add_users(instructor)

        self.client.force_authenticate(user=instructor)
        url = reverse('discussion-moderation-banned-users', kwargs={'course_id': str(self.course_key)})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('lms.djangoapps.discussion.rest_api.views.delete_course_post_for_user.apply_async')
    def test_bulk_delete_ban_feature_disabled(self, mock_task):
        """Test that ban is rejected when waffle flag is disabled."""
        with mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=False):
            self.client.force_authenticate(user=self.moderator)

            url = reverse('discussion-moderation-bulk-delete-ban')
            data = {
                'user_id': self.student.id,
                'course_id': str(self.course_key),
                'ban_user': True,
                'ban_scope': 'course',
                'reason': 'Spam content'
            }

            response = self.client.post(url, data, format='json')

            # Should return 403 when feature is disabled
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertIn('not enabled', response.data['error'].lower())

            # Verify task was not called
            mock_task.assert_not_called()

            # Verify no ban was created
            self.assertFalse(DiscussionBan.objects.filter(user=self.student).exists())

    @mock.patch('lms.djangoapps.discussion.rest_api.views.delete_course_post_for_user.apply_async')
    def test_bulk_delete_ban_feature_enabled(self, mock_task):
        """Test that ban works when waffle flag is enabled."""
        mock_task.return_value = mock.Mock(id='enabled-feature-task')

        with mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True):
            self.client.force_authenticate(user=self.moderator)

            url = reverse('discussion-moderation-bulk-delete-ban')
            data = {
                'user_id': self.student.id,
                'course_id': str(self.course_key),
                'ban_user': True,
                'ban_scope': 'course',
                'reason': 'Spam content'
            }

            response = self.client.post(url, data, format='json')

            # Should succeed when feature is enabled
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            # Verify task was called
            mock_task.assert_called_once()

    @mock.patch('lms.djangoapps.discussion.rest_api.views.delete_course_post_for_user.apply_async')
    def test_bulk_delete_without_ban_works_regardless_of_flag(self, mock_task):
        """Test that delete without ban works even when flag is disabled."""
        mock_task.return_value = mock.Mock(id='no-ban-task')

        with mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=False):
            self.client.force_authenticate(user=self.moderator)

            url = reverse('discussion-moderation-bulk-delete-ban')
            data = {
                'user_id': self.student.id,
                'course_id': str(self.course_key),
                'ban_user': False  # Not banning
            }

            response = self.client.post(url, data, format='json')

            # Should work fine - flag only controls ban feature
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            # Verify task was called
            mock_task.assert_called_once()


class DirectBanUserViewTest(UrlResetMixin, ModuleStoreTestCase):
    """Tests for the standalone ban_user endpoint (without bulk delete)."""

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.client = APIClient()

        # Create course
        self.course = CourseFactory.create(
            org='TestX',
            course='CS101',
            run='2024'
        )
        self.course_key = self.course.id

        # Create users
        self.student = UserFactory.create(username='student')
        self.moderator = UserFactory.create(username='moderator')
        self.admin = UserFactory.create(username='admin', is_staff=True)

        # Create enrollments
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course_key)
        CourseEnrollmentFactory.create(user=self.moderator, course_id=self.course_key)

        # Add moderator to course staff role
        CourseStaffRole(self.course_key).add_users(self.moderator)

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_course_level(self, mock_waffle):
        """Test banning a user at course level."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Posting spam'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['user_id'], self.student.id)
        self.assertEqual(response.data['scope'], 'course')
        self.assertIn('ban_id', response.data)

        # Verify ban was created
        ban = DiscussionBan.objects.get(user=self.student, course_id=self.course_key)
        self.assertTrue(ban.is_active)
        self.assertEqual(ban.scope, 'course')
        self.assertEqual(ban.reason, 'Posting spam')
        self.assertEqual(ban.banned_by, self.moderator)

        # Verify moderation log was created
        log = DiscussionModerationLog.objects.get(target_user=self.student)
        self.assertEqual(log.action_type, DiscussionModerationLog.ACTION_BAN)
        self.assertEqual(log.moderator, self.moderator)

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_with_username(self, mock_waffle):
        """Test banning a user by username instead of user_id."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'username': 'student',
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Posting spam'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'student')

        # Verify ban was created
        ban = DiscussionBan.objects.get(user=self.student)
        self.assertTrue(ban.is_active)

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_org_level_requires_global_staff(self, mock_waffle):
        """Test that org-level bans require global staff permissions."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'organization',
            'reason': 'Cross-course spam'
        }

        response = self.client.post(url, data, format='json')

        # Moderator should not have permission for org-level ban
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify no ban was created
        self.assertFalse(DiscussionBan.objects.filter(user=self.student).exists())

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_org_level_with_global_staff(self, mock_waffle):
        """Test that global staff can create org-level bans."""
        self.client.force_authenticate(user=self.admin)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'organization',
            'reason': 'Spam across multiple courses'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['scope'], 'organization')

        # Verify org-level ban was created
        ban = DiscussionBan.objects.get(user=self.student)
        self.assertEqual(ban.scope, 'organization')
        self.assertEqual(ban.org_key, self.course_key.org)
        self.assertIsNone(ban.course_id)

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_already_banned(self, mock_waffle):
        """Test that banning an already banned user returns an error."""
        # Create existing ban
        DiscussionBan.objects.create(
            user=self.student,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='First ban',
            is_active=True
        )

        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Second ban attempt'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already banned', response.data['error'])

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_reactivates_inactive_ban(self, mock_waffle):
        """Test that banning a previously unbanned user reactivates the ban."""
        from django.utils import timezone

        # Create inactive ban
        inactive_ban = DiscussionBan.objects.create(
            user=self.student,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Original ban',
            is_active=False,
            unbanned_at=timezone.now(),
            unbanned_by=self.admin
        )

        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Reactivating ban'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('reactivated', response.data['message'])

        # Verify ban was reactivated
        inactive_ban.refresh_from_db()
        self.assertTrue(inactive_ban.is_active)
        self.assertEqual(inactive_ban.reason, 'Reactivating ban')
        self.assertIsNone(inactive_ban.unbanned_at)
        self.assertIsNone(inactive_ban.unbanned_by)

        # Verify moderation log
        log = DiscussionModerationLog.objects.filter(
            target_user=self.student,
            action_type=DiscussionModerationLog.ACTION_BAN_REACTIVATE
        ).first()
        self.assertIsNotNone(log)

    def test_ban_user_permission_denied_for_student(self):
        """Test that students cannot ban users."""
        self.client.force_authenticate(user=self.student)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.moderator.id,
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Student trying to ban'
        }

        response = self.client.post(url, data, format='json')

        # Should fail permission check
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Verify no ban was created
        self.assertFalse(DiscussionBan.objects.filter(user=self.moderator).exists())

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_nonexistent_user(self, mock_waffle):
        """Test banning a non-existent user."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': 99999,
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Test'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('does not exist', response.data['error'])

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=False)
    def test_ban_user_feature_disabled(self, mock_waffle):
        """Test that banning fails when feature flag is disabled."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'course',
            'reason': 'Test'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('not enabled', response.data['error'])

    @mock.patch.object(ENABLE_DISCUSSION_BAN, 'is_enabled', return_value=True)
    def test_ban_user_optional_reason(self, mock_waffle):
        """Test that reason is optional for ban."""
        self.client.force_authenticate(user=self.moderator)

        url = reverse('discussion-moderation-ban-user')
        data = {
            'user_id': self.student.id,
            'course_id': str(self.course_key),
            'scope': 'course'
            # No reason provided
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify ban was created with empty reason
        ban = DiscussionBan.objects.get(user=self.student)
        self.assertEqual(ban.reason, '')

