"""
Tests for tasks in import_from_modulestore app.
"""
from django.core.exceptions import ObjectDoesNotExist
from organizations.models import Organization
from openedx_learning.api.authoring_models import LearningPackage
from unittest.mock import patch

from cms.djangoapps.import_from_modulestore.data import ImportStatus
from cms.djangoapps.import_from_modulestore.tasks import (
    import_staged_content_to_library_task,
    save_legacy_content_to_staged_content_task,
)
from openedx.core.djangoapps.content_libraries import api as content_libraries_api
from openedx.core.djangoapps.content_libraries.api import ContentLibrary
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

from .factories import ImportFactory


class ImportCourseToLibraryMixin(ModuleStoreTestCase):
    """
    Mixin for setting up data for tests.
    """

    def setUp(self):
        super().setUp()

        self.library = content_libraries_api.create_library(
            org=Organization.objects.create(name='Organization 1', short_name='org1'),
            slug='lib_1',
            title='Library Org 1',
            description='This is a library from Org 1',
        )
        self.content_library = ContentLibrary.objects.get_by_key(self.library.key)

        self.course = CourseFactory.create()
        self.chapter = BlockFactory.create(category='chapter', parent=self.course, display_name='Chapter 1')
        self.sequential = BlockFactory.create(category='sequential', parent=self.chapter, display_name='Sequential 1')
        self.vertical = BlockFactory.create(category='vertical', parent=self.sequential, display_name='Vertical 1')
        self.video = BlockFactory.create(category='video', parent=self.vertical, display_name='Video 1')
        self.problem = BlockFactory.create(category='problem', parent=self.vertical, display_name='Problem 1')

        # self.course2 = CourseFactory.create()
        # self.chapter2 = BlockFactory.create(category='chapter', parent=self.course, display_name='Chapter 2')
        self.chapter2 = BlockFactory.create(category='chapter', parent=self.course, display_name='Chapter 2')
        self.sequential2 = BlockFactory.create(category='sequential', parent=self.chapter2, display_name='Sequential 2')
        self.vertical2 = BlockFactory.create(category='vertical', parent=self.sequential2, display_name='Vertical 2')
        self.video2 = BlockFactory.create(category='video', parent=self.vertical2, display_name='Video 2')
        self.problem2 = BlockFactory.create(category='problem', parent=self.vertical2, display_name='Problem 2')

        self.import_event = ImportFactory(source_key=self.course.id)
        self.user = self.import_event.user


class TestSaveCourseSectionsToStagedContentTask(ImportCourseToLibraryMixin):
    """
    Test cases for save_course_sections_to_staged_content_task.
    """

    def test_save_legacy_content_to_staged_content_task(self):
        """
        End-to-end test for save_legacy_content_to_staged_content_task.
        """
        course_chapters_to_import = [self.chapter, self.chapter2]
        save_legacy_content_to_staged_content_task(self.import_event.uuid)

        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.staged_content_for_import.count(), len(course_chapters_to_import))
        self.assertEqual(self.import_event.status, ImportStatus.STAGED)

    def test_old_staged_content_deletion_before_save_new(self):
        """ Checking that repeated saving of the same content does not create duplicates. """
        course_chapters_to_import = [self.chapter, self.chapter2]

        save_legacy_content_to_staged_content_task(self.import_event.uuid)

        self.assertEqual(self.import_event.staged_content_for_import.count(), len(course_chapters_to_import))

        save_legacy_content_to_staged_content_task(self.import_event.uuid)

        self.assertEqual(self.import_event.staged_content_for_import.count(), len(course_chapters_to_import))


class TestImportLibraryFromStagedContentTask(ImportCourseToLibraryMixin):
    """
    Test cases for import_staged_content_to_library_task.
    """

    def _is_imported(self, library, xblock):
        library_learning_package = LearningPackage.objects.get(id=library.learning_package_id)
        self.assertTrue(library_learning_package.content_set.filter(text__icontains=xblock.display_name).exists())

    def test_import_staged_content_to_library_task(self):
        """ End-to-end test for import_staged_content_to_library_task. """
        library_learning_package = LearningPackage.objects.get(id=self.library.learning_package_id)
        self.assertEqual(library_learning_package.content_set.count(), 0)
        expected_imported_xblocks = [self.problem, self.problem2, self.video, self.video2]
        save_legacy_content_to_staged_content_task(self.import_event.uuid)

        import_staged_content_to_library_task(
            [str(self.chapter.location), str(self.chapter2.location)],
            self.import_event.uuid,
            self.content_library.learning_package.id,
            self.user.id,
            'component',
            override=True
        )

        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.status, ImportStatus.IMPORTED)

        for xblock in expected_imported_xblocks:
            self._is_imported(self.library, xblock)

        library_learning_package.refresh_from_db()
        self.assertEqual(library_learning_package.content_set.count(), len(expected_imported_xblocks))
        self.assertEqual(self.import_event.publishableentityimport_set.count(), len(expected_imported_xblocks))

    @patch('cms.djangoapps.import_from_modulestore.tasks.import_from_staged_content')
    def test_import_library_block_not_found(self, mock_import_from_staged_content):
        """ Test that if a block is not found in the staged content, it is not imported. """
        non_existent_usage_ids = ['block-v1:edX+Demo+2023+type@vertical+block@12345']
        save_legacy_content_to_staged_content_task(self.import_event.uuid)
        with self.allow_transaction_exception():
            with self.assertRaises(ObjectDoesNotExist):
                import_staged_content_to_library_task(
                    non_existent_usage_ids,
                    str(self.import_event.uuid),
                    self.content_library.learning_package.id,
                    self.user.id,
                    'component',
                    override=True,
                )
                mock_import_from_staged_content.assert_not_called()

    def test_cannot_import_staged_content_twice(self):
        """
        Tests if after importing staged content into the library,
        the staged content is deleted and cannot be imported again.
        """
        chapters_to_import = [self.chapter, self.chapter2]
        expected_imported_xblocks = [self.problem, self.video]
        save_legacy_content_to_staged_content_task(self.import_event.uuid)

        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.staged_content_for_import.count(), len(chapters_to_import))
        self.assertEqual(self.import_event.status, ImportStatus.STAGED)

        import_staged_content_to_library_task(
            [str(self.chapter.location)],
            str(self.import_event.uuid),
            self.content_library.learning_package.id,
            self.user.id,
            'component',
            override=True,
        )

        for xblock in expected_imported_xblocks:
            self._is_imported(self.library, xblock)

        library_learning_package = LearningPackage.objects.get(id=self.library.learning_package_id)
        self.assertEqual(library_learning_package.content_set.count(), len(expected_imported_xblocks))

        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.status, ImportStatus.IMPORTED)
        self.assertTrue(not self.import_event.staged_content_for_import.exists())
        self.assertEqual(self.import_event.publishableentityimport_set.count(), len(expected_imported_xblocks))
