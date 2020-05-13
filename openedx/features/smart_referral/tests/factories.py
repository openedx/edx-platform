import factory

from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.features.smart_referral.models import SmartReferral


class SmartReferralFactory(factory.django.DjangoModelFactory):
    """
    Factory for SmartReferral model. It contains fake data or sub-factories for mandatory fields
    """

    class Meta:
        model = SmartReferral

    user = factory.SubFactory(UserFactory)
    contact_email = factory.Faker('email')
