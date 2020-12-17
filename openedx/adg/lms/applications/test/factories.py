"""
All model factories for applications
"""
import factory

from openedx.adg.lms.applications.models import BusinessLine
from django.contrib.auth.models import User
from student.models import UserProfile
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile


class BusinessLineFactory(factory.DjangoModelFactory):
    """
    Factory for BusinessLine model
    """
    class Meta:
        model = BusinessLine

    title = factory.Faker('word')
    description = factory.Faker('sentence')


class UserFactory(factory.DjangoModelFactory):
    """
    Factory for User model
    """

    class Meta:
        model = User

    username = factory.Faker('name')
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)
    password = factory.Faker('password')


class ProfileFactory(factory.django.DjangoModelFactory):
    """
    Factory for UserProfile model
    """

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('name')
    city = factory.Faker('word')


class ExtendedProfileFactory(factory.django.DjangoModelFactory):
    """
    Factory for ExtendedUserProfile model
    """

    class Meta:
        model = ExtendedUserProfile

    user = factory.SubFactory(UserFactory)
    saudi_national = False
