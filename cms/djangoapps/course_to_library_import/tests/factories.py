"""
Factories for CourseToLibraryImport model.
"""

import factory
from factory.django import DjangoModelFactory

from common.djangoapps.student.tests.factories import UserFactory

from cms.djangoapps.course_to_library_import.models import CourseToLibraryImport


class CourseToLibraryImportFactory(DjangoModelFactory):
    """
    Factory for CourseToLibraryImport model.
    """
    class Meta:
        model = CourseToLibraryImport

    course_ids = ' '.join([f'course-v1:edX+DemoX+Demo_Course{i}' for i in range(1, 3)])
    library_key = 'library-key'
    source_type = 'source-type'
    metadata = {}
    user = factory.SubFactory(UserFactory)
