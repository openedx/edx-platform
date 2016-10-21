"""Factories for generating fake catalog data."""
from uuid import uuid4

import factory
from factory.fuzzy import FuzzyText


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

    key = FuzzyText(prefix='org/', suffix='/run')
    marketing_url = FuzzyText(prefix='https://www.example.com/marketing/')


class Course(factory.Factory):
    """
    Factory for stubbing Course resources from the catalog API.
    """
    class Meta(object):
        model = dict

    title = FuzzyText(prefix='Course ')
    key = FuzzyText(prefix='course+')
    owners = [Organization()]
    course_runs = [CourseRun() for __ in range(3)]


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

    uuid = str(uuid4())
    title = FuzzyText(prefix='Program ')
    subtitle = FuzzyText(prefix='Subtitle ')
    type = 'FooBar'
    marketing_slug = FuzzyText(prefix='slug_')
    authoring_organizations = [Organization()]
    courses = [Course() for __ in range(3)]
    banner_image = {
        size: BannerImage() for size in ['large', 'medium', 'small', 'x-small']
    }
