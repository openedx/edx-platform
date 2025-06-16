"""
Factories for creating test data for the modulestore migrator.
"""
import uuid

import factory
from opaque_keys.edx.keys import LearningContextKey
from openedx_learning.api.authoring_models import LearningPackage
from organizations.tests.factories import OrganizationFactory

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.modulestore_migrator.models import ModulestoreSource, ModulestoreMigration
from openedx.core.djangoapps.content_libraries.api import ContentLibrary


class LearningPackageFactory(factory.django.DjangoModelFactory):
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


class ContentLibraryFactory(factory.django.DjangoModelFactory):
    """
    Factory for ContentLibrary model.
    """

    class Meta:
        model = ContentLibrary

    org = factory.SubFactory(OrganizationFactory)
    license = factory.Faker('sentence')
    slug = factory.Faker('slug')
    learning_package = factory.SubFactory(LearningPackageFactory)


class ModulestoreSourceFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating ModulestoreSource instances.
    """
    class Meta:
        model = ModulestoreSource
    forwarded_by = None

    @factory.lazy_attribute
    def key(self):
        return LearningContextKey.from_string(f"course-v1:edX+DemoX+{uuid.uuid4()}")


class ModulestoreMigrationFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating ModulestoreMigration instances.
    """
    class Meta:
        model = ModulestoreMigration

    source = factory.SubFactory(ModulestoreSourceFactory)
    user = factory.SubFactory(UserFactory)
