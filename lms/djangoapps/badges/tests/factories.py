"""
Factories for Badge tests
"""


from random import random

import factory
from django.core.files.base import ContentFile
from factory.django import ImageField

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.badges.models import (  # lint-amnesty, pylint: disable=line-too-long
    BadgeAssertion,
    BadgeClass,
    CourseCompleteImageConfiguration,
    CourseEventBadgesConfiguration
)


def generate_dummy_image(_unused):
    """
    Used for image fields to create a sane default.
    """
    return ContentFile(
        ImageField()._make_data(  # pylint: disable=protected-access
            {'color': 'blue', 'width': 50, 'height': 50, 'format': 'PNG'}
        ), 'test.png'
    )


class CourseCompleteImageConfigurationFactory(factory.django.DjangoModelFactory):
    """
    Factory for BadgeImageConfigurations
    """
    class Meta:
        model = CourseCompleteImageConfiguration

    mode = 'honor'
    icon = factory.LazyAttribute(generate_dummy_image)


class BadgeClassFactory(factory.django.DjangoModelFactory):
    """
    Factory for BadgeClass
    """
    class Meta:
        model = BadgeClass

    slug = 'test_slug'
    badgr_server_slug = 'test_badgr_server_slug'
    issuing_component = 'test_component'
    display_name = 'Test Badge'
    description = "Yay! It's a test badge."
    criteria = 'https://example.com/syllabus'
    mode = 'honor'
    image = factory.LazyAttribute(generate_dummy_image)


class RandomBadgeClassFactory(BadgeClassFactory):
    """
    Same as BadgeClassFactory, but randomize the slug.
    """
    slug = factory.lazy_attribute(lambda _: 'test_slug_' + str(random()).replace('.', '_'))


class BadgeAssertionFactory(factory.django.DjangoModelFactory):
    """
    Factory for BadgeAssertions
    """
    class Meta:
        model = BadgeAssertion

    user = factory.SubFactory(UserFactory)
    badge_class = factory.SubFactory(RandomBadgeClassFactory)
    data = {}
    assertion_url = 'http://example.com/example.json'
    image_url = 'http://example.com/image.png'


class CourseEventBadgesConfigurationFactory(factory.django.DjangoModelFactory):
    """
    Factory for CourseEventsBadgesConfiguration
    """
    class Meta:
        model = CourseEventBadgesConfiguration

    enabled = True
