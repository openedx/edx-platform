"""Provides factories for User API models."""
from factory.django import DjangoModelFactory
from factory import SubFactory
from student.tests.factories import UserFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from ..models import UserPreference, UserCourseTag, UserOrgTag


# Factories are self documenting
# pylint: disable=missing-docstring
class UserPreferenceFactory(DjangoModelFactory):
    class Meta(object):
        model = UserPreference

    user = None
    key = None
    value = "default test value"


class UserCourseTagFactory(DjangoModelFactory):
    class Meta(object):
        model = UserCourseTag

    user = SubFactory(UserFactory)
    course_id = SlashSeparatedCourseKey('org', 'course', 'run')
    key = None
    value = None


class UserOrgTagFactory(DjangoModelFactory):
    """ Simple factory class for generating UserOrgTags """
    class Meta(object):
        model = UserOrgTag

    user = SubFactory(UserFactory)
    org = 'org'
    key = None
    value = None
