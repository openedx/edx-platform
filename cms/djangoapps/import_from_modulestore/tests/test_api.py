"""
Test cases for import_from_modulestore.api module.
"""
from unittest.mock import patch

import pytest
from opaque_keys.edx.keys import CourseKey
from organizations.models import Organization

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.import_from_modulestore.api import import_staged_content_to_library, stage_content_for_import
from cms.djangoapps.import_from_modulestore.data import ImportStatus
from cms.djangoapps.import_from_modulestore.models import Import
from openedx.core.djangoapps.content_libraries import api as content_libraries_api
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from .factories import ImportFactory


@pytest.mark.django_db
class TestCourseToLibraryImportAPI(ModuleStoreTestCase):
    """
    Test cases for Import API.
    """

    def setUp(self):
        super().setUp()

        _library_metadata = content_libraries_api.create_library(
            org=Organization.objects.create(name='Organization 1', short_name='org1'),
            slug='lib_1',
            title='Library Org 1',
            description='This is a library from Org 1',
        )
        self.library = content_libraries_api.ContentLibrary.objects.get_by_key(_library_metadata.key)

    def test_stage_content_for_import(self):
        """
        Test stage_content_for_import function.
        """
        course_id = "course-v1:edX+DemoX+Demo_Course"
        user = UserFactory()
        stage_content_for_import(course_id, user.id)

        import_event = Import.objects.get()
        assert import_event.source_key == CourseKey.from_string(course_id)
        assert import_event.user_id == user.id
        assert import_event.status == ImportStatus.NOT_STARTED

    def test_import_staged_content_to_library(self):
        """
        Test import_staged_content_to_library function with different override values.
        """
        import_event = ImportFactory(
            source_key=CourseKey.from_string("course-v1:edX+DemoX+Demo_Course"),
        )
        usage_ids = [
            "block-v1:edX+DemoX+Demo_Course+type@chapter+block@123",
            "block-v1:edX+DemoX+Demo_Course+type@chapter+block@456",
        ]
        override = False

        with patch(
            "cms.djangoapps.import_from_modulestore.api.import_staged_content_to_library_task"
        ) as import_staged_content_to_library_task_mock:
            import_staged_content_to_library(
                usage_ids,
                import_event.uuid,
                self.library.learning_package.id,
                import_event.user.id,
                "xblock",
                override
            )

        import_staged_content_to_library_task_mock.apply_async.assert_called_once_with(
            kwargs={
                "usage_key_strings": usage_ids,
                "import_uuid": import_event.uuid,
                "learning_package_id": self.library.learning_package.id,
                "user_id": import_event.user.id,
                "composition_level": "xblock",
                "override": override,
            },
        )

    def test_import_staged_content_to_library_invalid_usage_key(self):
        """
        Test import_staged_content_to_library function with not chapter usage keys.
        """
        import_event = ImportFactory(
            source_key=CourseKey.from_string("course-v1:edX+DemoX+Demo_Course"),
        )
        usage_ids = [
            "block-v1:edX+DemoX+Demo_Course+type@problem+block@123",
            "block-v1:edX+DemoX+Demo_Course+type@vertical+block@456",
        ]

        with patch(
            "cms.djangoapps.import_from_modulestore.api.import_staged_content_to_library_task"
        ) as import_staged_content_to_library_task_mock:
            with self.assertRaises(ValueError):
                import_staged_content_to_library(
                    usage_ids,
                    import_event.uuid,
                    self.library.learning_package.id,
                    import_event.user.id,
                    "xblock",
                    False
                )
        import_staged_content_to_library_task_mock.apply_async.assert_not_called()
