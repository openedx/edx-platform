"""
Test data factories for Idea app models
"""
import factory

from lms.djangoapps.onboarding.tests.factories import OrganizationFactory, UserFactory
from openedx.features.idea.constants import CITY_MAX_LENGTH, OVERVIEW_MAX_LENGTH, TITLE_MAX_LENGTH
from openedx.features.idea.models import Idea, Location, OrganizationBase


class LocationFactory(factory.django.DjangoModelFactory):
    """Factory for location abstract model"""

    class Meta(object):
        model = Location
        abstract = True

    country = 'PK'
    city = factory.Faker('pystr', min_chars=1, max_chars=CITY_MAX_LENGTH)


class OrganizationBaseFactory(factory.django.DjangoModelFactory):
    """Factory for organization base abstract model"""

    class Meta(object):
        model = OrganizationBase
        abstract = True
        django_get_or_create = ('user', 'organization')

    organization = factory.SubFactory(OrganizationFactory)
    organization_mission = factory.Faker('word')


class IdeaFactory(OrganizationBaseFactory, LocationFactory):
    """Factory for idea model. It contains fake data or sub-factories for all mandatory fields"""

    class Meta(object):
        model = Idea

    user = factory.SubFactory(UserFactory)
    title = factory.Faker('pystr', min_chars=1, max_chars=TITLE_MAX_LENGTH)
    overview = factory.Faker('pystr', min_chars=1, max_chars=OVERVIEW_MAX_LENGTH)
    description = factory.Faker('word')
