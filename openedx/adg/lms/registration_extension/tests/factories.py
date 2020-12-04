"""
Factories for registration-extension app
"""
import factory

from openedx.adg.lms.applications.test.factories import BusinessLineFactory
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from student.tests.factories import UserFactory


class ExtendedUserProfileFactory(factory.DjangoModelFactory):
    """
    Factory for ExtendedUserProfile model
    """

    class Meta:
        model = ExtendedUserProfile

    user = factory.SubFactory(UserFactory)
    company = factory.SubFactory(BusinessLineFactory)
