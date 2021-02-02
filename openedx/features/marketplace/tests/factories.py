"""
All model factories for marketplace
"""
import factory

from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.features.idea.tests.factories import LocationFactory, OrganizationBaseFactory
from openedx.features.marketplace.models import MarketplaceRequest


class ChallengeFactory(OrganizationBaseFactory, LocationFactory):
    """Factory for MarketplaceRequest model. It contains fake data or sub-factories for all mandatory fields"""

    class Meta(object):
        model = MarketplaceRequest

    user = factory.SubFactory(UserFactory)
    resources_currently_using = factory.Faker('word')
    description = factory.Faker('word')
    approach_to_address = factory.Faker('word')
    organization_sector = ['health']
    organizational_problems = ['healthcare', 'other value']
    user_services = ['healthcare-supplies', 'other value']
