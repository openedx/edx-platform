"""
Tests for tasks in import_from_modulestore app.
"""
from unittest.mock import patch, call
import uuid

from openedx_learning.api.authoring_models import LearningPackage
from organizations.models import Organization
from user_tasks.models import UserTaskStatus

from cms.djangoapps.import_from_modulestore.data import ImportStatus
from cms.djangoapps.import_from_modulestore.tasks import (
    import_staged_content_to_library,
    save_leagacy_content_to_staged_content,
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
        self.import_event.user_task_status = UserTaskStatus.objects.create(
            user=self.user,
            task_id=uuid.uuid4(),
            task_class='cms.djangoapps.import_from_modulestore.import_from_modulestore.tasks.import_to_library_task',
            name='Test',
            total_steps=2,
        )
        self.import_event.save()


class TestSaveCourseSectionsToStagedContentTask(ImportCourseToLibraryMixin):
    """
    Test cases for save_course_sections_to_staged_content_task.
    """

    @patch('cms.djangoapps.import_from_modulestore.models.Import.set_status')
    def test_save_legacy_content_to_staged_content_task(self, mock_set_status):
        """
        End-to-end test for save_legacy_content_to_staged_content_task.
        """
        course_chapters_to_import = [self.chapter, self.chapter2]
        save_leagacy_content_to_staged_content(self.import_event)

        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.staged_content_for_import.count(), len(course_chapters_to_import))
        staging_calls = [
            call(ImportStatus.WAITNG_TO_STAGE),
            call(ImportStatus.STAGING),
            call(ImportStatus.STAGED),
        ]
        self.assertEqual(mock_set_status.call_count, len(staging_calls))
        mock_set_status.assert_has_calls(staging_calls)

    @patch('cms.djangoapps.import_from_modulestore.models.Import.clean_related_staged_content')
    def test_old_staged_content_deletion_before_save_new(self, mock_clean_related_staged_content):
        """ Checking that repeated saving of the same content does not create duplicates. """
        course_chapters_to_import = [self.chapter, self.chapter2]

        save_leagacy_content_to_staged_content(self.import_event)

        mock_clean_related_staged_content.assert_called_once()
        self.import_event.refresh_from_db()

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

        save_leagacy_content_to_staged_content(self.import_event)
        import_staged_content_to_library(
            self.import_event,
            self.content_library.learning_package.id,
            [str(self.chapter.location), str(self.chapter2.location)],
        )

        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.user_task_status.state, ImportStatus.IMPORTED.value)

        for xblock in expected_imported_xblocks:
            self._is_imported(self.library, xblock)

        library_learning_package.refresh_from_db()
        self.assertEqual(library_learning_package.content_set.count(), len(expected_imported_xblocks))
        self.assertEqual(self.import_event.publishableentityimport_set.count(), len(expected_imported_xblocks))

    @patch('cms.djangoapps.import_from_modulestore.tasks.import_from_staged_content')
    def test_import_library_block_not_found(self, mock_import_from_staged_content):
        """ Test that if a block is not found in the staged content, it is not imported. """
        non_existent_usage_ids = ['block-v1:edX+Demo+2023+type@vertical+block@12345']
        with self.allow_transaction_exception():
            import_staged_content_to_library(
                self.import_event,
                self.content_library.learning_package.id,
                non_existent_usage_ids,
            )
            mock_import_from_staged_content.assert_not_called()

    def test_cannot_import_staged_content_twice(self):
        """
        Tests if after importing staged content into the library,
        the staged content is deleted and cannot be imported again.
        """
        chapters_to_import = [self.chapter, self.chapter2]
        expected_imported_xblocks = [self.problem, self.video]

        save_leagacy_content_to_staged_content(self.import_event)
        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.staged_content_for_import.count(), len(chapters_to_import))
        self.assertEqual(self.import_event.user_task_status.state, ImportStatus.STAGED.value)

        import_staged_content_to_library(
            self.import_event,
            self.content_library.learning_package.id,
            [str(self.chapter.location)],
        )
        for xblock in expected_imported_xblocks:
            self._is_imported(self.library, xblock)

        # try importing again, should not be possible
        self.import_event.refresh_from_db()
        import_staged_content_to_library(
            self.import_event,
            self.content_library.learning_package.id,
            [str(self.chapter.location)],
        )
        self.import_event.refresh_from_db()
        self.assertEqual(self.import_event.user_task_status.state, ImportStatus.IMPORTING_FAILED.value)
