import factory

from lms.djangoapps.onboarding.tests.factories import OrganizationFactory, UserFactory
from openedx.features.idea.models import Idea


class IdeaFactory(factory.django.DjangoModelFactory):
    """Factory for idea model. It contains fake data or sub-factories for all mandatory fields"""

    class Meta(object):
        model = Idea
        django_get_or_create = ('user', 'organization')

    user = factory.SubFactory(UserFactory)
    title = factory.Faker('pystr', min_chars=1, max_chars=50)
    overview = factory.Faker('pystr', min_chars=1, max_chars=150)
    description = factory.Faker('word')
    organization = factory.SubFactory(OrganizationFactory)
    organization_mission = factory.Faker('word')
    country = 'PK'
    city = factory.Faker('pystr', min_chars=1, max_chars=255)
