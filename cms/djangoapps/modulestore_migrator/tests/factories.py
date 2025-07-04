"""
Factories for creating test data for the modulestore migrator.
"""
import uuid

import factory
from opaque_keys.edx.keys import LearningContextKey

from cms.djangoapps.modulestore_migrator.models import ModulestoreSource


class ModulestoreSourceFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating ModulestoreSource instances.
    """
    class Meta:
        model = ModulestoreSource

    @factory.lazy_attribute
    def key(self):
        return LearningContextKey.from_string(f"course-v1:edX+DemoX+{uuid.uuid4()}")
