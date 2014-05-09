"""Provides factories for User API models."""
from factory.django import DjangoModelFactory
from factory import SubFactory
from student.tests.factories import UserFactory
from user_api.models import UserPreference, UserCourseTag
from xmodule.modulestore.locations import SlashSeparatedCourseKey

# Factories don't have __init__ methods, and are self documenting
# pylint: disable=W0232, C0111
class UserPreferenceFactory(DjangoModelFactory):
    FACTORY_FOR = UserPreference

    user = None
    key = None
    value = "default test value"


class UserCourseTagFactory(DjangoModelFactory):
    FACTORY_FOR = UserCourseTag

    user = SubFactory(UserFactory)
    course_id = SlashSeparatedCourseKey('org', 'course', 'run')
    key = None
    value = None
