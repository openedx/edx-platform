"""
All model factories for applications
"""
import factory

from openedx.adg.lms.applications.models import BusinessLine


class BusinessLineFactory(factory.DjangoModelFactory):
    """
    Factory for BusinessLine model
    """
    class Meta:
        model = BusinessLine

    title = factory.Faker('word')
    description = factory.Faker('sentence')
