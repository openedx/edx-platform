""" Tests for course reindex command """
import ddt
from django.core.management import call_command, CommandError
import mock

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory

from contentstore.management.commands.reindex_course import Command as ReindexCommand
from contentstore.courseware_index import SearchIndexingError


@ddt.ddt
class TestReindexCourse(ModuleStoreTestCase):
    """ Tests for course reindex command """
    def setUp(self):
        """ Setup method - create courses """
        super(TestReindexCourse, self).setUp()
        self.store = modulestore()
        self.first_lib = LibraryFactory.create(
            org="test", library="lib1", display_name="run1", default_store=ModuleStoreEnum.Type.split
        )
        self.second_lib = LibraryFactory.create(
            org="test", library="lib2", display_name="run2", default_store=ModuleStoreEnum.Type.split
        )

        self.first_course = CourseFactory.create(
            org="test", course="course1", display_name="run1"
        )
        self.second_course = CourseFactory.create(
            org="test", course="course2", display_name="run1"
        )

    REINDEX_PATH_LOCATION = 'contentstore.management.commands.reindex_course.CoursewareSearchIndexer.do_course_reindex'
    MODULESTORE_PATCH_LOCATION = 'contentstore.management.commands.reindex_course.modulestore'
    YESNO_PATCH_LOCATION = 'contentstore.management.commands.reindex_course.query_yes_no'

    def _get_lib_key(self, library):
        """ Get's library key as it is passed to indexer """
        return library.location.library_key

    def _build_calls(self, *courses):
        """ Builds a list of mock.call instances representing calls to reindexing method """
        return [mock.call(self.store, course.id) for course in courses]

    def test_given_no_arguments_raises_command_error(self):
        """ Test that raises CommandError for incorrect arguments """
        with self.assertRaisesRegexp(CommandError, ".* requires one or more arguments.*"):
            call_command('reindex_course')

    @ddt.data('qwerty', 'invalid_key', 'xblockv1:qwerty')
    def test_given_invalid_course_key_raises_not_found(self, invalid_key):
        """ Test that raises InvalidKeyError for invalid keys """
        err_string = "Invalid course_key: '{0}'".format(invalid_key)
        with self.assertRaisesRegexp(CommandError, err_string):
            call_command('reindex_course', invalid_key)

    def test_given_library_key_raises_command_error(self):
        """ Test that raises CommandError if library key is passed """
        with self.assertRaisesRegexp(CommandError, ".* is not a course key"):
            call_command('reindex_course', unicode(self._get_lib_key(self.first_lib)))

        with self.assertRaisesRegexp(CommandError, ".* is not a course key"):
            call_command('reindex_course', unicode(self._get_lib_key(self.second_lib)))

        with self.assertRaisesRegexp(CommandError, ".* is not a course key"):
            call_command(
                'reindex_course',
                unicode(self.second_course.id),
                unicode(self._get_lib_key(self.first_lib))
            )

    def test_given_id_list_indexes_courses(self):
        """ Test that reindexes courses when given single course key or a list of course keys """
        with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index, \
                mock.patch(self.MODULESTORE_PATCH_LOCATION, mock.Mock(return_value=self.store)):
            call_command('reindex_course', unicode(self.first_course.id))
            self.assertEqual(patched_index.mock_calls, self._build_calls(self.first_course))
            patched_index.reset_mock()

            call_command('reindex_course', unicode(self.second_course.id))
            self.assertEqual(patched_index.mock_calls, self._build_calls(self.second_course))
            patched_index.reset_mock()

            call_command(
                'reindex_course',
                unicode(self.first_course.id),
                unicode(self.second_course.id)
            )
            expected_calls = self._build_calls(self.first_course, self.second_course)
            self.assertEqual(patched_index.mock_calls, expected_calls)

    def test_given_all_key_prompts_and_reindexes_all_courses(self):
        """ Test that reindexes all courses when --all key is given and confirmed """
        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index, \
                    mock.patch(self.MODULESTORE_PATCH_LOCATION, mock.Mock(return_value=self.store)):
                call_command('reindex_course', all=True)

                patched_yes_no.assert_called_once_with(ReindexCommand.CONFIRMATION_PROMPT, default='no')
                expected_calls = self._build_calls(self.first_course, self.second_course)
                self.assertItemsEqual(patched_index.mock_calls, expected_calls)

    def test_given_all_key_prompts_and_reindexes_all_courses_cancelled(self):
        """ Test that does not reindex anything when --all key is given and cancelled """
        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = False
            with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index, \
                    mock.patch(self.MODULESTORE_PATCH_LOCATION, mock.Mock(return_value=self.store)):
                call_command('reindex_course', all=True)

                patched_yes_no.assert_called_once_with(ReindexCommand.CONFIRMATION_PROMPT, default='no')
                patched_index.assert_not_called()

    def test_fail_fast_if_reindex_fails(self):
        """ Test that fails on first reindexing exception """
        with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index:
            patched_index.side_effect = SearchIndexingError("message", [])

            with self.assertRaises(SearchIndexingError):
                call_command('reindex_course', unicode(self.second_course.id))
