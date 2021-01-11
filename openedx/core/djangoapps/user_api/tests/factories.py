"""Provides factories for User API models."""


from factory import SubFactory
from factory.django import DjangoModelFactory
from opaque_keys.edx.locator import CourseLocator

from common.djangoapps.student.tests.factories import UserFactory

from ..models import UserCourseTag, UserOrgTag, UserPreference


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
    course_id = CourseLocator('org', 'course', 'run')
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
