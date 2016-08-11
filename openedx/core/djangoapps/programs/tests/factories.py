"""Factories for generating fake program-related data."""
import factory
from factory.fuzzy import FuzzyText


class Program(factory.Factory):
    """
    Factory for stubbing program resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    id = factory.Sequence(lambda n: n)  # pylint: disable=invalid-name
    name = FuzzyText(prefix='Program ')
    subtitle = FuzzyText(prefix='Subtitle ')
    category = 'FooBar'
    status = 'unpublished'
    marketing_slug = FuzzyText(prefix='slug_')
    organizations = []
    course_codes = []
    banner_image_urls = {}


class Organization(factory.Factory):
    """
    Factory for stubbing nested organization resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    key = FuzzyText(prefix='org_')
    display_name = FuzzyText(prefix='Display Name ')


class CourseCode(factory.Factory):
    """
    Factory for stubbing nested course code resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    display_name = FuzzyText(prefix='Display Name ')
    run_modes = []


class RunMode(factory.Factory):
    """
    Factory for stubbing nested run mode resources from the Programs API (v1).
    """
    class Meta(object):
        model = dict

    course_key = FuzzyText(prefix='org/', suffix='/run')
    mode_slug = 'verified'


class Progress(factory.Factory):
    """
    Factory for stubbing program progress dicts.
    """
    class Meta(object):
        model = dict

    id = factory.Sequence(lambda n: n)  # pylint: disable=invalid-name
    completed = []
    in_progress = []
    not_started = []
