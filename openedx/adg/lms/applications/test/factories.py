"""
All model factories for applications
"""
import factory

from openedx.adg.lms.applications.models import BusinessLine
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from student.tests.factories import UserFactory


class BusinessLineFactory(factory.DjangoModelFactory):
    """
    Factory for BusinessLine model
    """
    class Meta:
        model = BusinessLine

    title = factory.Faker('word')
    description = factory.Faker('sentence')


class ExtendedUserProfileFactory(factory.django.DjangoModelFactory):
    """
    Factory for ExtendedUserProfile model
    """

    class Meta:
        model = ExtendedUserProfile

    user = factory.SubFactory(UserFactory)
    saudi_national = False
