"""
Factories for Import model.
"""
import uuid

import factory
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.import_from_modulestore.data import CompositionLevel
from cms.djangoapps.import_from_modulestore.models import Import


class ImportFactory(DjangoModelFactory):
    """
    Factory for Import model.
    """

    class Meta:
        model = Import

    @factory.lazy_attribute
    def source_key(self):
        return CourseKey.from_string(f'course-v1:edX+DemoX+{uuid.uuid4()}')

    user = factory.SubFactory(UserFactory)
    composition_level = CompositionLevel.COMPONENT.value
    override = False
