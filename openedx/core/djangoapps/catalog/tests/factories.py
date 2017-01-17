"""Factories for generating fake catalog data."""
from uuid import uuid4

import factory
from factory.fuzzy import FuzzyText
from xmodule.modulestore.tests.factories import CourseFactory


class Organization(factory.Factory):
    """
    Factory for stubbing Organization resources from the catalog API.
    """

    class Meta(object):
        model = dict

    name = FuzzyText(prefix='Organization ')
    key = FuzzyText(suffix='X')


class CourseRun(factory.Factory):
    """
    Factory for stubbing CourseRun resources from the catalog API.
    """

    class Meta(object):
        model = dict

    marketing_url = FuzzyText(prefix='https://www.example.com/marketing/')

    @factory.lazy_attribute
    def key(self):  # pylint: disable=missing-docstring
        return str(CourseFactory.create().id)


class Course(factory.Factory):
    """
    Factory for stubbing Course resources from the catalog API.
    """

    class Meta(object):
        model = dict

    title = FuzzyText(prefix='Course ')
    key = FuzzyText(prefix='course+')

    @factory.lazy_attribute
    def owners(self):  # pylint: disable=missing-docstring
        return Organization.create_batch(3)

    @factory.lazy_attribute
    def course_runs(self):  # pylint: disable=missing-docstring
        return CourseRun.create_batch(3)


class BannerImage(factory.Factory):
    """
    Factory for stubbing BannerImage resources from the catalog API.
    """

    class Meta(object):
        model = dict

    url = FuzzyText(
        prefix='https://www.somecdn.com/media/programs/banner_images/',
        suffix='.jpg'
    )


class Program(factory.Factory):
    """
    Factory for stubbing Program resources from the catalog API.
    """

    class Meta(object):
        model = dict

    title = FuzzyText(prefix='Program ')
    subtitle = FuzzyText(prefix='Subtitle ')
    type = 'FooBar'
    marketing_slug = FuzzyText(prefix='slug_')

    @factory.lazy_attribute
    def uuid(self):  # pylint: disable=missing-docstring
        # NOTE (CCB): We return a string here since nearly all of our tests will be testing for that
        # data type rather than UUID.
        return uuid4().hex

    @factory.lazy_attribute
    def authoring_organizations(self):  # pylint: disable=missing-docstring
        return [Organization()]

    @factory.lazy_attribute
    def courses(self):  # pylint: disable=missing-docstring
        return Course.create_batch(3)

    @factory.lazy_attribute
    def banner_image(self):  # pylint: disable=missing-docstring
        return {
            size: BannerImage() for size in ['large', 'medium', 'small', 'x-small']
            }


class ProgramType(factory.Factory):
    """
    Factory for stubbing ProgramType resources from the catalog API.
    """

    class Meta(object):
        model = dict

    name = FuzzyText()
    logo_image = FuzzyText(prefix='https://example.com/program/logo')
