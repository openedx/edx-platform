"""
Model factories for unit testing views or models.
"""

import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey

from student.tests.factories import UserFactory
from openedx.features.course_rating.models import CourseRating, CourseAverageRating

USER_PASSWORD = 'TEST_PASSOWRD'


class CourseRatingFactory(DjangoModelFactory):
    """
    Crete user with the given credentials.
    """
    class Meta(object):
        model = CourseRating
        django_get_or_create = ('course', 'user', 'rating', 'comment')

    course = CourseKey.from_string('course-v1:edX+DemoX+Demo_Course')
    user = factory.SubFactory(UserFactory)
    moderated_by = factory.SubFactory(UserFactory)
    rating = 5
    comment = factory.Sequence(u'This is test comment {0}'.format)
    is_approved = False


class CourseAverageRatingFactory(DjangoModelFactory):
    """
    Create course average rating for the given course.
    """
    class Meta(object):
        model = CourseAverageRating

    course = CourseKey.from_string('course-v1:edX+DemoX+Demo_Course')
    average_rating = 4
    total_raters = 2
