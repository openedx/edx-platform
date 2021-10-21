"""
Tests for Course Rating API serializers.
"""
from django.test import TestCase

from opaque_keys.edx.keys import CourseKey
from student.tests.factories import UserFactory
from openedx.features.course_rating.tests.factories import CourseRatingFactory
from openedx.features.course_rating.api.v1.serializers import CourseRatingSerializer


class CourseRatingSerializerTests(TestCase):
    """
    Unit tests for `CourseRatingSerializer`.
    """

    def setUp(self):
        self.user = UserFactory()
        self.moderator = UserFactory(username='moderator')
        self.course_rating = CourseRatingFactory(
            user=self.user,
            course=CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'),
            moderated_by=self.moderator,
            rating=3
        )
        self.expected_data = {
            'user': self.user.id,
            'id': 1,
            'rating': 3,
            'comment': 'This is test comment 0',
            'moderated_by': self.moderator.id,
            'is_approved': False,
            'course_rating': {'total_raters': 1, 'average_rating': '3.00'},
            'course': 'course-v1:edX+DemoX+Demo_Course'
        }
        super(CourseRatingSerializerTests, self).setUp()

    def test_user_data(self):
        """
        Tests response for `CourseRatingSerializer`.
        """
        serializer = CourseRatingSerializer(self.course_rating)
        assert serializer.data == self.expected_data
