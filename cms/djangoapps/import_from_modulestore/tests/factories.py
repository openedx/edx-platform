"""
Factories for Import model.
"""

import uuid

import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.import_from_modulestore.models import Import


class ImportFactory(DjangoModelFactory):
    """
    Factory for Import model.
    """

    class Meta:
        model = Import

    @factory.lazy_attribute
    def source_key(self):
        return CourseKey.from_string(f'course-v1:edX+DemoX+{self.uuid}')

    uuid = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user = factory.SubFactory(UserFactory)
