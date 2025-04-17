"""
Factories for content_libraries models.
"""
import factory
import uuid
from factory.django import DjangoModelFactory
from organizations.tests.factories import OrganizationFactory

from openedx_learning.api.authoring_models import LearningPackage
from openedx.core.djangoapps.content_libraries.api import ContentLibrary


class LearningPackageFactory(DjangoModelFactory):
    """
    Factory for LearningPackage model.
    """

    class Meta:
        model = LearningPackage

    title = factory.Faker('sentence')
    description = factory.Faker('sentence')
    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    created = factory.Faker('date_time')
    updated = factory.Faker('date_time')


class ContentLibraryFactory(DjangoModelFactory):
    """
    Factory for ContentLibrary model.
    """

    class Meta:
        model = ContentLibrary

    org = factory.SubFactory(OrganizationFactory)
    license = factory.Faker('sentence')
    slug = factory.Faker('slug')
    learning_package = factory.SubFactory(LearningPackageFactory)
