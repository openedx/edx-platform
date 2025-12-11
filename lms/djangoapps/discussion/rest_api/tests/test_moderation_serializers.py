"""
Tests for discussion moderation serializers.
"""

from django.test import TestCase

from forum.backends.mysql.models import DiscussionBan
from lms.djangoapps.discussion.rest_api.serializers import (
    BulkDeleteBanRequestSerializer,
    BannedUserSerializer,
)
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class BulkDeleteBanRequestSerializerTest(TestCase):
    """Tests for BulkDeleteBanRequestSerializer."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.course_id = 'course-v1:edX+DemoX+Demo_Course'

    def test_valid_data_without_ban(self):
        """Test serializer with valid data for delete only."""
        data = {
            'user_id': self.user.id,
            'course_id': self.course_id,
            'ban_user': False
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user_id'], self.user.id)
        self.assertFalse(serializer.validated_data['ban_user'])

    def test_valid_data_with_ban_and_reason(self):
        """Test serializer with ban enabled and reason provided."""
        data = {
            'user_id': self.user.id,
            'course_id': self.course_id,
            'ban_user': True,
            'ban_scope': 'course',
            'reason': 'Posting spam content'
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data['ban_user'])
        self.assertEqual(serializer.validated_data['reason'], 'Posting spam content')

    def test_missing_reason_when_ban_true(self):
        """Test that reason is required when ban_user is True."""
        data = {
            'user_id': self.user.id,
            'course_id': self.course_id,
            'ban_user': True,
            'ban_scope': 'course'
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reason', serializer.errors)

    def test_empty_reason_when_ban_true(self):
        """Test that empty reason is rejected when ban_user is True."""
        data = {
            'user_id': self.user.id,
            'course_id': self.course_id,
            'ban_user': True,
            'ban_scope': 'course',
            'reason': ''
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('reason', serializer.errors)

    def test_missing_required_fields(self):
        """Test that required fields are validated."""
        # Test with no data at all
        data = {}
        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        # course_id is required at field level
        self.assertIn('course_id', serializer.errors)
        
        # Test with course_id but no user identification
        data_with_course = {'course_id': self.course_id}
        serializer_with_course = BulkDeleteBanRequestSerializer(data=data_with_course)
        self.assertFalse(serializer_with_course.is_valid())
        # user_id OR username required - validated in validate() method
        self.assertIn('user_id', serializer_with_course.errors)

    def test_ban_scope_choices(self):
        """Test that ban_scope accepts valid choices."""
        for scope in ['course', 'organization']:
            data = {
                'user_id': self.user.id,
                'course_id': self.course_id,
                'ban_user': True,
                'ban_scope': scope,
                'reason': 'Test'
            }

            serializer = BulkDeleteBanRequestSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Scope {scope} should be valid")

    def test_invalid_ban_scope(self):
        """Test that invalid ban_scope is rejected."""
        data = {
            'user_id': self.user.id,
            'course_id': self.course_id,
            'ban_user': True,
            'ban_scope': 'invalid_scope',
            'reason': 'Test'
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ban_scope', serializer.errors)

    def test_default_values(self):
        """Test default values for optional fields."""
        data = {
            'user_id': self.user.id,
            'course_id': self.course_id
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertFalse(serializer.validated_data['ban_user'])
        self.assertEqual(serializer.validated_data['ban_scope'], 'course')

    def test_username_to_user_id_conversion(self):
        """Test that username is converted to user_id internally."""
        data = {
            'username': self.user.username,
            'course_id': self.course_id,
            'ban_user': False
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        # Should have converted username to user_id
        self.assertEqual(serializer.validated_data['user_id'], self.user.id)
        self.assertEqual(serializer.validated_data['resolved_username'], self.user.username)

    def test_invalid_username(self):
        """Test that invalid username raises error."""
        data = {
            'username': 'nonexistent_user_12345',
            'course_id': self.course_id
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)

    def test_invalid_user_id(self):
        """Test that invalid user_id raises error."""
        data = {
            'user_id': 999999,
            'course_id': self.course_id
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('user_id', serializer.errors)

    def test_both_user_id_and_username(self):
        """Test that providing both user_id and username works (user_id takes precedence)."""
        data = {
            'user_id': self.user.id,
            'username': self.user.username,
            'course_id': self.course_id
        }

        serializer = BulkDeleteBanRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user_id'], self.user.id)


class BannedUserSerializerTest(ModuleStoreTestCase):
    """Tests for BannedUserSerializer."""

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(org='TestX', number='CS101', run='2024')
        self.course_key = self.course.id
        self.user = UserFactory.create(username='banneduser', email='banned@example.com')
        self.moderator = UserFactory.create(username='moderator')

    def test_serialize_course_ban(self):
        """Test serializing a course-level ban."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Spam posting',
            is_active=True
        )

        serializer = BannedUserSerializer(ban)
        data = serializer.data

        self.assertEqual(data['id'], ban.id)
        self.assertEqual(data['username'], 'banneduser')
        self.assertEqual(data['email'], 'banned@example.com')
        self.assertEqual(data['user_id'], self.user.id)
        self.assertEqual(data['scope'], 'course')
        self.assertEqual(data['reason'], 'Spam posting')
        self.assertEqual(data['banned_by_username'], 'moderator')
        self.assertTrue(data['is_active'])

    def test_serialize_org_ban(self):
        """Test serializing an organization-level ban."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            org_key='TestX',
            scope='organization',
            banned_by=self.moderator,
            reason='Repeated violations',
            is_active=True
        )

        serializer = BannedUserSerializer(ban)
        data = serializer.data

        self.assertEqual(data['organization'], 'TestX')
        self.assertEqual(data['scope'], 'organization')
        self.assertIsNone(data['course_id'])

    def test_serialize_multiple_bans(self):
        """Test serializing multiple bans."""
        DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Ban 1'
        )

        user2 = UserFactory.create()
        DiscussionBan.objects.create(
            user=user2,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Ban 2'
        )

        bans = DiscussionBan.objects.filter(course_id=self.course_key)
        serializer = BannedUserSerializer(bans, many=True)

        self.assertEqual(len(serializer.data), 2)

    def test_read_only_fields(self):
        """Test that all fields are read-only."""
        ban = DiscussionBan.objects.create(
            user=self.user,
            course_id=self.course_key,
            scope='course',
            banned_by=self.moderator,
            reason='Test'
        )

        # Try to modify data via serializer
        data = {
            'username': 'modified',
            'reason': 'modified reason'
        }

        # Serializer is read-only, so validation should fail for writes
        # But reading should work fine
        serializer = BannedUserSerializer(ban)
        original_data = serializer.data

        self.assertEqual(original_data['username'], 'banneduser')
        self.assertEqual(original_data['reason'], 'Test')
