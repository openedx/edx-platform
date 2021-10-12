"""
Tests for course_rating django models.
"""

from unittest import TestCase
import pytest

from opaque_keys.edx.keys import CourseKey
from student.tests.factories import UserFactory
from openedx.features.course_rating.models import CourseRating
from openedx.features.course_rating.tests.factories import CourseRatingFactory

pytestmark = pytest.mark.django_db


class CourseRatingModelTests(TestCase):
    """
   Unit tests for "CourseRating" model.
   """
    def setUp(self):
        self.user = UserFactory(username='test-rating')
        self.course = CourseKey.from_string('course-v1:edX+DemoX+Demo_Course')
        self.rating = 5
        super(CourseRatingModelTests, self).setUp()

    def test_string_representation(self):
        """
       Test "CourseRating" model string representation.
       """
        CourseRatingFactory(
            user=self.user,
            course=CourseKey.from_string('course-v1:edX+DemoX+Demo_Course'),
            rating=self.rating
        )
        course_rating = CourseRating.objects.filter(user=self.user).first()

        expected_string = '{user}: ({course} - {rating})'.format(
            user=self.user,
            course=self.course,
            rating=self.rating
        )
        assert expected_string == str(course_rating)
