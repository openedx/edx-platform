"""
Tests for AI Learning API.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.features.ai_learning import api as ai_api
from openedx.features.ai_learning.models import (
    AdaptiveInteraction,
    AIGeneratedCourse,
    StudentLearningProfile,
)

User = get_user_model()


class TestGenerateCourse(TestCase):
    """Tests for generate_course API function."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_pass'
        )

    @mock.patch('openedx.features.ai_learning.api.AIEngineClient')
    def test_generate_course_success(self, mock_client_class):
        """Test successful course generation."""
        mock_client = mock_client_class.return_value
        mock_client.generate_curriculum.return_value = {
            'course_id': 'ai_course_123',
            'status': 'generating'
        }

        ai_course = ai_api.generate_course(
            user=self.user,
            prompt="Create a course on Python programming",
            course_org="TestX",
            course_number="CS101",
            course_run="2025"
        )

        self.assertIsInstance(ai_course, AIGeneratedCourse)
        self.assertEqual(ai_course.generation_status, 'generating')
        self.assertEqual(ai_course.ai_engine_course_id, 'ai_course_123')
        self.assertEqual(ai_course.creator, self.user)

    def test_generate_course_empty_prompt(self):
        """Test that empty prompt raises ValueError."""
        with self.assertRaises(ValueError):
            ai_api.generate_course(
                user=self.user,
                prompt="",
                course_org="TestX",
                course_number="CS101",
                course_run="2025"
            )


class TestStudentLearningProfile(TestCase):
    """Tests for student learning profile API."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='test_pass'
        )

    @mock.patch('openedx.features.ai_learning.api.AIEngineClient')
    def test_get_or_create_profile(self, mock_client_class):
        """Test getting or creating a student profile."""
        mock_client = mock_client_class.return_value

        profile = ai_api.get_student_learning_profile(self.user)

        self.assertIsInstance(profile, StudentLearningProfile)
        self.assertEqual(profile.user, self.user)
        self.assertTrue(mock_client.create_student_profile.called)

    def test_get_existing_profile(self):
        """Test getting an existing profile."""
        existing_profile = StudentLearningProfile.objects.create(
            user=self.user,
            ai_engine_profile_id=f"user_{self.user.id}"
        )

        profile = ai_api.get_student_learning_profile(self.user)

        self.assertEqual(profile.id, existing_profile.id)


class TestAdaptiveInteractions(TestCase):
    """Tests for adaptive interaction recording."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='student',
            email='student@example.com',
            password='test_pass'
        )
        self.course_key = CourseKey.from_string('course-v1:edX+DemoX+Demo')
        self.usage_key = UsageKey.from_string(
            'block-v1:edX+DemoX+Demo+type@problem+block@test'
        )

    @mock.patch('openedx.features.ai_learning.api.AIEngineClient')
    def test_record_interaction(self, mock_client_class):
        """Test recording an adaptive interaction."""
        mock_client = mock_client_class.return_value
        mock_client.record_interaction.return_value = {
            'analysis': 'Student is performing well',
            'adaptations': []
        }

        interaction = ai_api.record_adaptive_interaction(
            user=self.user,
            course_key=self.course_key,
            usage_key=self.usage_key,
            interaction_type='assessment',
            interaction_data={'score': 0.9, 'time_spent': 120}
        )

        self.assertIsInstance(interaction, AdaptiveInteraction)
        self.assertEqual(interaction.user, self.user)
        self.assertEqual(interaction.course_key, self.course_key)
        self.assertEqual(interaction.interaction_type, 'assessment')
        self.assertGreater(interaction.response_time_ms, 0)
