"""
Tests for Course Rating API serializers.
"""
from django.test import TestCase

from opaque_keys.edx.keys import CourseKey
from student.tests.factories import UserFactory
from openedx.features.course_rating.tests.factories import CourseRatingFactory
from openedx.features.course_rating.api.v1.serializers import (
    CourseAverageRatingListSerializer,
    CourseRatingSerializer,
)
from openedx.features.course_rating.models import CourseAverageRating


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

            'id': 1,
            'user': self.user.id,
            'rating': 3,
            'comment': 'This is test comment 0',
            'moderated_by': self.moderator.id,
            'is_approved': False,
            'course_rating': {
                'average_rating': '3.00',
                'total_raters': 1
            },
            'course': 'course-v1:edX+DemoX+Demo_Course',
            'course_title': '',
            'username': self.user.username
        }
        super(CourseRatingSerializerTests, self).setUp()

    def test_review_data(self):
        """
        Tests response for `CourseRatingSerializer`.
        """
        serializer = CourseRatingSerializer(self.course_rating)
        assert serializer.data == self.expected_data


class CourseAverageRatingListSerializerTests(TestCase):
    """
    Unit tests for `CourseAverageRatingListSerializer`.
    """

    def setUp(self):
        self.user = UserFactory()
        self.moderator = UserFactory(username='moderator2')
        self.course = 'course-v1:edX+DemoX+Demo_Course'
        self.course_rating = CourseRatingFactory(
            user=self.user,
            course=CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'),
            moderated_by=self.moderator,
            rating=3
        )
        self.expected_data = {
            'total_raters': 1,
            'course': 'course-v1:edX+DemoX+Demo_Course',
            'average_rating': '3.00'
        }
        super(CourseAverageRatingListSerializerTests, self).setUp()

    def test_course_data(self):
        """
        Tests response for `CourseAverageRatingListSerializerTests`.
        """
        course_average_rating = CourseAverageRating.objects.filter(course=self.course).first()
        serializer = CourseAverageRatingListSerializer(course_average_rating)
        assert serializer.data == self.expected_data
