import factory
from openedx.features.idea.tests.factories import OrganizationBaseFactory, LocationFactory
from openedx.features.marketplace.models import MarketplaceRequest

from lms.djangoapps.onboarding.tests.factories import UserFactory


class ChallengeFactory(OrganizationBaseFactory, LocationFactory):
    """Factory for idea model. It contains fake data or sub-factories for all mandatory fields"""

    class Meta:
        model = MarketplaceRequest

    user = factory.SubFactory(UserFactory)
    resources_currently_using = factory.Faker('word')
    description = factory.Faker('word')
    approach_to_address = factory.Faker('word')
    organization_sector = ['health']
    organizational_problems = ['healthcare', 'other value']
    user_services = ['healthcare-supplies', 'other value']
