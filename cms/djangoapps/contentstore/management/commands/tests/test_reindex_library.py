""" Tests for library reindex command """
import ddt
from django.core.management import call_command, CommandError
import mock

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from common.test.utils import nostderr
from xmodule.modulestore.tests.factories import CourseFactory, LibraryFactory

from opaque_keys import InvalidKeyError

from contentstore.management.commands.reindex_library import Command as ReindexCommand
from contentstore.courseware_index import SearchIndexingError


@ddt.ddt
class TestReindexLibrary(ModuleStoreTestCase):
    """ Tests for library reindex command """
    def setUp(self):
        """ Setup method - create libraries and courses """
        super(TestReindexLibrary, self).setUp()
        self.store = modulestore()
        self.first_lib = LibraryFactory.create(
            org="test", library="lib1", display_name="run1", default_store=ModuleStoreEnum.Type.split
        )
        self.second_lib = LibraryFactory.create(
            org="test", library="lib2", display_name="run2", default_store=ModuleStoreEnum.Type.split
        )

        self.first_course = CourseFactory.create(
            org="test", course="course1", display_name="run1", default_store=ModuleStoreEnum.Type.split
        )
        self.second_course = CourseFactory.create(
            org="test", course="course2", display_name="run1", default_store=ModuleStoreEnum.Type.split
        )

    REINDEX_PATH_LOCATION = 'contentstore.management.commands.reindex_library.LibrarySearchIndexer.do_library_reindex'
    MODULESTORE_PATCH_LOCATION = 'contentstore.management.commands.reindex_library.modulestore'
    YESNO_PATCH_LOCATION = 'contentstore.management.commands.reindex_library.query_yes_no'

    def _get_lib_key(self, library):
        """ Get's library key as it is passed to indexer """
        return library.location.library_key

    def _build_calls(self, *libraries):
        """ BUilds a list of mock.call instances representing calls to reindexing method """
        return [mock.call(self.store, self._get_lib_key(lib)) for lib in libraries]

    def test_given_no_arguments_raises_command_error(self):
        """ Test that raises CommandError for incorrect arguments """
        with self.assertRaises(SystemExit), nostderr():
            with self.assertRaisesRegexp(CommandError, ".* requires one or more arguments .*"):
                call_command('reindex_library')

    @ddt.data('qwerty', 'invalid_key', 'xblock-v1:qwe+rty')
    def test_given_invalid_lib_key_raises_not_found(self, invalid_key):
        """ Test that raises InvalidKeyError for invalid keys """
        with self.assertRaises(InvalidKeyError):
            call_command('reindex_library', invalid_key)

    def test_given_course_key_raises_command_error(self):
        """ Test that raises CommandError if course key is passed """
        with self.assertRaises(SystemExit), nostderr():
            with self.assertRaisesRegexp(CommandError, ".* is not a library key"):
                call_command('reindex_library', unicode(self.first_course.id))

        with self.assertRaises(SystemExit), nostderr():
            with self.assertRaisesRegexp(CommandError, ".* is not a library key"):
                call_command('reindex_library', unicode(self.second_course.id))

        with self.assertRaises(SystemExit), nostderr():
            with self.assertRaisesRegexp(CommandError, ".* is not a library key"):
                call_command(
                    'reindex_library',
                    unicode(self.second_course.id),
                    unicode(self._get_lib_key(self.first_lib))
                )

    def test_given_id_list_indexes_libraries(self):
        """ Test that reindexes libraries when given single library key or a list of library keys """
        with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index, \
                mock.patch(self.MODULESTORE_PATCH_LOCATION, mock.Mock(return_value=self.store)):
            call_command('reindex_library', unicode(self._get_lib_key(self.first_lib)))
            self.assertEqual(patched_index.mock_calls, self._build_calls(self.first_lib))
            patched_index.reset_mock()

            call_command('reindex_library', unicode(self._get_lib_key(self.second_lib)))
            self.assertEqual(patched_index.mock_calls, self._build_calls(self.second_lib))
            patched_index.reset_mock()

            call_command(
                'reindex_library',
                unicode(self._get_lib_key(self.first_lib)),
                unicode(self._get_lib_key(self.second_lib))
            )
            expected_calls = self._build_calls(self.first_lib, self.second_lib)
            self.assertEqual(patched_index.mock_calls, expected_calls)

    def test_given_all_key_prompts_and_reindexes_all_libraries(self):
        """ Test that reindexes all libraries when --all key is given and confirmed """
        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = True
            with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index, \
                    mock.patch(self.MODULESTORE_PATCH_LOCATION, mock.Mock(return_value=self.store)):
                call_command('reindex_library', all=True)

                patched_yes_no.assert_called_once_with(ReindexCommand.CONFIRMATION_PROMPT, default='no')
                expected_calls = self._build_calls(self.first_lib, self.second_lib)
                self.assertItemsEqual(patched_index.mock_calls, expected_calls)

    def test_given_all_key_prompts_and_reindexes_all_libraries_cancelled(self):
        """ Test that does not reindex anything when --all key is given and cancelled """
        with mock.patch(self.YESNO_PATCH_LOCATION) as patched_yes_no:
            patched_yes_no.return_value = False
            with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index, \
                    mock.patch(self.MODULESTORE_PATCH_LOCATION, mock.Mock(return_value=self.store)):
                call_command('reindex_library', all=True)

                patched_yes_no.assert_called_once_with(ReindexCommand.CONFIRMATION_PROMPT, default='no')
                patched_index.assert_not_called()

    def test_fail_fast_if_reindex_fails(self):
        """ Test that fails on first reindexing exception """
        with mock.patch(self.REINDEX_PATH_LOCATION) as patched_index:
            patched_index.side_effect = SearchIndexingError("message", [])

            with self.assertRaises(SearchIndexingError):
                call_command('reindex_library', unicode(self._get_lib_key(self.second_lib)))
