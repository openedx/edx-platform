"""Factories for generating fake embargo data."""

import factory
from factory.django import DjangoModelFactory
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import Country, CountryAccessRule, RestrictedCourse


class CountryFactory(DjangoModelFactory):
    class Meta(object):
        model = Country

    country = 'US'


class RestrictedCourseFactory(DjangoModelFactory):
    class Meta(object):
        model = RestrictedCourse

    @factory.lazy_attribute
    def course_key(self):
        return CourseFactory().id


class CountryAccessRuleFactory(DjangoModelFactory):
    class Meta(object):
        model = CountryAccessRule

    country = factory.SubFactory(CountryFactory)
    restricted_course = factory.SubFactory(RestrictedCourseFactory)
    rule_type = CountryAccessRule.BLACKLIST_RULE
