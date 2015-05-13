"""
Factories for Bookmark models.
"""

from factory.django import DjangoModelFactory
from factory import SubFactory
from functools import partial

from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from ..models import Bookmark

COURSE_KEY = SlashSeparatedCourseKey(u'edX', u'test_course', u'test')
LOCATION = partial(COURSE_KEY.make_usage_key, u'problem')


class BookmarkFactory(DjangoModelFactory):
    """ Simple factory class for generating Bookmark """
    FACTORY_FOR = Bookmark

    user = SubFactory(UserFactory)
    course_key = COURSE_KEY
    usage_key = LOCATION('usage_id')
    display_name = ""
    path = list()
