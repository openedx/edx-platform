"""
All model factories for applications
"""
import factory

from openedx.adg.lms.applications.models import ApplicationHub, BusinessLine, UserApplication
from student.tests.factories import UserFactory


class BusinessLineFactory(factory.DjangoModelFactory):
    """
    Factory for BusinessLine model
    """

    class Meta:
        model = BusinessLine

    title = factory.Faker('word')
    description = factory.Faker('sentence')


class UserApplicationFactory(factory.DjangoModelFactory):
    """
    Factory for UserApplication model
    """

    class Meta:
        model = UserApplication

    user = factory.SubFactory(UserFactory)
    business_line = factory.SubFactory(BusinessLineFactory)
    organization = 'testOrganization'


class ApplicationHubFactory(factory.DjangoModelFactory):
    """
    Factory for ApplicationHub Model
    """

    class Meta:
        model = ApplicationHub
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
