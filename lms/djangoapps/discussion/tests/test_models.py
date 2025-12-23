"""
Tests for discussion moderation models.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from forum.backends.mysql.models import (
    DiscussionBan,
    DiscussionBanException,
    ModerationAuditLog,
)
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

User = get_user_model()


class DiscussionBanModelTest(ModuleStoreTestCase):
    """Tests for DiscussionBan model."""

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(org='TestX', number='CS101', run='2024')
        self.course_key = self.course.id
        self.user = UserFactory.create(username='testuser')
        self.moderator = UserFactory.create(username='moderator')

    def test_create_course_level_ban(self):
        """Test creating a course-level ban."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Spam posting',
            is_active=True
        )

        self.assertEqual(ban.user, self.user)
        self.assertEqual(ban.course_id, self.course_key)
        self.assertEqual(ban.scope, 'course')
        self.assertEqual(ban.banned_by, self.moderator)
        self.assertTrue(ban.is_active)
        self.assertIsNotNone(ban.banned_at)
        self.assertIsNone(ban.unbanned_at)

    def test_create_organization_level_ban(self):
        """Test creating an organization-level ban."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Repeated violations',
            is_active=True
        )

        self.assertEqual(ban.scope, 'organization')
        self.assertEqual(ban.org_key, 'TestX')
        self.assertIsNone(ban.course_id)

    def test_unique_constraint_course_ban(self):
        """Test that duplicate active course-level bans are prevented."""
        DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='First ban',
            is_active=True
        )

        with self.allow_transaction_exception():
            with self.assertRaises(IntegrityError):
                DiscussionBan.objects.create(
                    user=self.user,
                    course_id=self.course_key,
                    scope='course',
                    banned_by=self.moderator,
                    reason='Second ban',
                    is_active=True
                )

    def test_unique_constraint_allows_inactive_duplicates(self):
        """Test that inactive bans don't violate unique constraint."""
        DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='First ban',
            is_active=False
        )

        # Should not raise IntegrityError
        ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Second ban',
            is_active=True
        )

        self.assertTrue(ban.is_active)

    def test_clean_course_ban_requires_course_id(self):
        """Test that course-level bans require course_id."""
        ban = DiscussionBan(
            user=self.user,
            scope='course',
            banned_by=self.moderator,
            reason='Test'
        )

        with self.assertRaises(ValidationError):
            ban.clean()

    def test_clean_org_ban_requires_organization(self):
        """Test that organization-level bans require organization."""
        ban = DiscussionBan(
            user=self.user,
            scope='organization',
            banned_by=self.moderator,
            reason='Test'
        )

        with self.assertRaises(ValidationError):
            ban.clean()

    def test_clean_org_ban_rejects_course_id(self):
        """Test that organization-level bans should not have course_id."""
        ban = DiscussionBan(
            user=self.user,
            course_id=self.course_key,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Test'
        )

        with self.assertRaises(ValidationError):
            ban.clean()

    def test_is_user_banned_course_level(self):
        """Test is_user_banned for course-level bans."""
        self.assertFalse(DiscussionBan.is_user_banned(self.user, self.course_key))

        DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Test',
            is_active=True
        )

        self.assertTrue(DiscussionBan.is_user_banned(self.user, self.course_key))

    def test_is_user_banned_organization_level(self):
        """Test is_user_banned for organization-level bans."""
        DiscussionBan.objects.create(
            user=self.user,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Test',
            is_active=True
        )

        self.assertTrue(DiscussionBan.is_user_banned(self.user, self.course_key))

    def test_is_user_banned_with_exception(self):
        """Test that ban exceptions override organization-level bans."""
        org_ban = DiscussionBan.objects.create(
            user=self.user,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Test',
            is_active=True
        )

        # User is banned
        self.assertTrue(DiscussionBan.is_user_banned(self.user, self.course_key))

        # Create exception for this course
        DiscussionBanException.objects.create(
            ban=org_ban,
            course_id=self.course_key,
            unbanned_by=self.moderator,
            reason='Exception for CS101'
        )

        # User is no longer banned in this course
        self.assertFalse(DiscussionBan.is_user_banned(self.user, self.course_key))

    def test_str_representation_course(self):
        """Test string representation of course-level ban."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Test'
        )

        expected = f"Ban: {self.user.username} in {self.course_key} (course-level)"
        self.assertEqual(str(ban), expected)

    def test_str_representation_org(self):
        """Test string representation of organization-level ban."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Test'
        )

        expected = f"Ban: {self.user.username} in TestX (org-level)"
        self.assertEqual(str(ban), expected)


class DiscussionBanExceptionModelTest(ModuleStoreTestCase):
    """Tests for DiscussionBanException model."""

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(org='TestX', number='CS101', run='2024')
        self.course_key = self.course.id
        self.user = UserFactory.create()
        self.moderator = UserFactory.create()

        self.org_ban = DiscussionBan.objects.create(
            user=self.user,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Org-level ban'
        )

    def test_create_exception(self):
        """Test creating a ban exception."""
        exception = DiscussionBanException.objects.create(
            ban=self.org_ban,
            course_id=self.course_key,
            unbanned_by=self.moderator,
            reason='Special exception'
        )

        self.assertEqual(exception.ban, self.org_ban)
        self.assertEqual(exception.course_id, self.course_key)
        self.assertEqual(exception.unbanned_by, self.moderator)

    def test_unique_constraint(self):
        """Test that duplicate exceptions are prevented."""
        DiscussionBanException.objects.create(
            ban=self.org_ban,
            course_id=self.course_key,
            unbanned_by=self.moderator
        )

        with self.allow_transaction_exception():
            with self.assertRaises(IntegrityError):
                DiscussionBanException.objects.create(
                    ban=self.org_ban,
                    course_id=self.course_key,
                    unbanned_by=self.moderator
                )

    def test_clean_requires_org_ban(self):
        """Test that exceptions only work for organization-level bans."""
        course_ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Course ban'
        )

        exception = DiscussionBanException(
            ban=course_ban,
            course_id=self.course_key,
            unbanned_by=self.moderator
        )

        with self.assertRaises(ValidationError):
            exception.clean()

    def test_str_representation(self):
        """Test string representation."""
        exception = DiscussionBanException.objects.create(
            ban=self.org_ban,
            course_id=self.course_key,
            unbanned_by=self.moderator
        )

        expected = f"Exception: {self.user.username} allowed in {self.course_key}"
        self.assertEqual(str(exception), expected)


class ModerationAuditLogModelTest(ModuleStoreTestCase):
    """Tests for ModerationAuditLog model."""

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        self.course_key = self.course.id
        self.user = UserFactory.create()
        self.moderator = UserFactory.create()

    def test_create_human_ban_log(self):
        """Test creating a human moderator ban action log."""
        log = ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_BAN,
            source=ModerationAuditLog.SOURCE_HUMAN,
            target_user=self.user,
            moderator=self.moderator,
            course_id=str(self.course_key),
            scope='course',
            reason='Spam',
            metadata={'posts_deleted': 10}
        )

        self.assertEqual(log.action_type, 'ban_user')
        self.assertEqual(log.source, 'human')
        self.assertEqual(log.target_user, self.user)
        self.assertEqual(log.moderator, self.moderator)
        self.assertEqual(log.metadata['posts_deleted'], 10)

    def test_create_unban_log(self):
        """Test creating an unban action log."""
        log = ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_UNBAN,
            source=ModerationAuditLog.SOURCE_HUMAN,
            target_user=self.user,
            moderator=self.moderator,
            course_id=str(self.course_key),
            scope='course',
            reason='Appeal approved'
        )

        self.assertEqual(log.action_type, 'unban_user')
        self.assertEqual(log.source, 'human')

    def test_create_ai_moderation_log(self):
        """Test creating an AI moderation action log."""
        log = ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_FLAGGED,
            source=ModerationAuditLog.SOURCE_AI,
            original_author=self.user,
            body='This is spam content',
            course_id=str(self.course_key),
            classification='spam',
            confidence_score=0.95,
            reasoning='Content matches spam patterns',
            classifier_output={'category': 'spam', 'score': 0.95},
            actions_taken=['flagged', 'soft_deleted']
        )

        self.assertEqual(log.action_type, 'flagged')
        self.assertEqual(log.source, 'ai')
        self.assertEqual(log.original_author, self.user)
        self.assertEqual(log.classification, 'spam')
        self.assertEqual(log.confidence_score, 0.95)

    def test_query_by_target_user(self):
        """Test querying logs by target user."""
        ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_BAN,
            source=ModerationAuditLog.SOURCE_HUMAN,
            target_user=self.user,
            moderator=self.moderator,
            course_id=str(self.course_key)
        )

        logs = ModerationAuditLog.objects.filter(target_user=self.user)
        self.assertEqual(logs.count(), 1)

    def test_query_by_source(self):
        """Test querying logs by moderation source."""
        ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_BAN,
            source=ModerationAuditLog.SOURCE_HUMAN,
            target_user=self.user,
            moderator=self.moderator,
            course_id=str(self.course_key)
        )
        ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_FLAGGED,
            source=ModerationAuditLog.SOURCE_AI,
            original_author=self.user,
            body='Spam content',
            course_id=str(self.course_key)
        )

        human_logs = ModerationAuditLog.objects.filter(source=ModerationAuditLog.SOURCE_HUMAN)
        ai_logs = ModerationAuditLog.objects.filter(source=ModerationAuditLog.SOURCE_AI)

        self.assertEqual(human_logs.count(), 1)
        self.assertEqual(ai_logs.count(), 1)

    def test_to_dict_human_moderation(self):
        """Test to_dict method for human moderation."""
        log = ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_BAN,
            source=ModerationAuditLog.SOURCE_HUMAN,
            target_user=self.user,
            moderator=self.moderator,
            course_id=str(self.course_key),
            reason='Test reason'
        )

        data = log.to_dict()
        self.assertEqual(data['action_type'], 'ban_user')
        self.assertEqual(data['source'], 'human')
        self.assertEqual(data['target_user_id'], str(self.user.pk))
        self.assertEqual(data['target_user_username'], self.user.username)
        self.assertEqual(data['moderator_username'], self.moderator.username)

    def test_to_dict_ai_moderation(self):
        """Test to_dict method for AI moderation."""
        log = ModerationAuditLog.objects.create(
            action_type=ModerationAuditLog.ACTION_FLAGGED,
            source=ModerationAuditLog.SOURCE_AI,
            original_author=self.user,
            body='Spam content',
            course_id=str(self.course_key),
            classification='spam',
            confidence_score=0.95
        )

        data = log.to_dict()
        self.assertEqual(data['action_type'], 'flagged')
        self.assertEqual(data['source'], 'ai')
        self.assertEqual(data['original_author_id'], str(self.user.pk))
        self.assertEqual(data['body'], 'Spam content')
        self.assertEqual(data['classification'], 'spam')
        self.assertEqual(data['confidence_score'], 0.95)
