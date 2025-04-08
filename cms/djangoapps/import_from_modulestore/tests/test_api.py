"""
Test cases for import_from_modulestore.api module.
"""

from unittest.mock import patch

import pytest
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.import_from_modulestore.api import create_import, import_course_staged_content_to_library
from cms.djangoapps.import_from_modulestore.data import ImportStatus
from cms.djangoapps.import_from_modulestore.models import Import
from openedx.core.djangoapps.content_libraries.tests import factories
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from .factories import ImportFactory


@pytest.mark.django_db
class TestCourseToLibraryImportAPI(ModuleStoreTestCase):
    """
    Test cases for Import API.
    """

    def setUp(self):
        super().setUp()

        self.library = factories.ContentLibraryFactory()

    def test_create_import(self):
        """
        Test create_import function.
        """
        course_id = "course-v1:edX+DemoX+Demo_Course"
        user = UserFactory()
        create_import(course_id, user.id, self.library.learning_package_id)

        import_event = Import.objects.get()
        assert import_event.source_key == CourseKey.from_string(course_id)
        assert import_event.target == self.library.learning_package
        assert import_event.user_id == user.id
        assert import_event.status == ImportStatus.PENDING

    def test_import_course_staged_content_to_library(self):
        """
        Test import_course_staged_content_to_library function with different override values.
        """
        import_event = ImportFactory(
            target=self.library.learning_package,
            source_key=CourseKey.from_string("course-v1:edX+DemoX+Demo_Course"),
        )
        usage_ids = [
            "block-v1:edX+DemoX+Demo_Course+type@html+block@123",
            "block-v1:edX+DemoX+Demo_Course+type@html+block@456",
        ]
        override = False

        with patch(
            "cms.djangoapps.import_from_modulestore.api.import_course_staged_content_to_library_task"
        ) as import_course_staged_content_to_library_task_mock:
            import_course_staged_content_to_library(
                usage_ids,
                import_event.uuid,
                import_event.user.id,
                'xblock',
                override
            )

        import_course_staged_content_to_library_task_mock.apply_async.assert_called_once_with(
            kwargs={
                'usage_ids': usage_ids,
                'import_uuid': import_event.uuid,
                'user_id': import_event.user.id,
                'composition_level': 'xblock',
                'override': override,
            },
        )
