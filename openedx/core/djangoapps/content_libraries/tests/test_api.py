"""
Tests for Content Library internal api.
"""

import base64
import hashlib
from unittest import mock

from django.test import TestCase

from opaque_keys.edx.keys import (
    CourseKey,
    UsageKey,
)
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryLocatorV2
from openedx_events.content_authoring.data import (
    ContentObjectChangedData,
    LibraryCollectionData,
    LibraryContainerData,
)
from openedx_events.content_authoring.signals import (
    CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
    LIBRARY_COLLECTION_CREATED,
    LIBRARY_COLLECTION_DELETED,
    LIBRARY_COLLECTION_UPDATED,
    LIBRARY_CONTAINER_UPDATED,
)
from openedx_learning.api import authoring as authoring_api

from .. import api
from ..models import ContentLibrary
from .base import ContentLibrariesRestApiTest


class EdxModulestoreImportClientTest(TestCase):
    """
    Tests for course importing APIs.
    """

    def setUp(self):
        """
        Setup mocks and the test client.
        """
        super().setUp()
        self.mock_library = mock.MagicMock()
        self.modulestore_mock = mock.MagicMock()
        self.client = api.EdxModulestoreImportClient(
            modulestore_instance=self.modulestore_mock,
            library=self.mock_library
        )

    def test_instantiate_without_args(self):
        """
        When instantiated without args,
        Then raises.
        """
        with self.assertRaises(ValueError):
            api.EdxModulestoreImportClient()

    def test_import_blocks_from_course_without_course(self):
        """
        Given no course,
        Then raises.
        """
        self.modulestore_mock.get_course.return_value.get_children.return_value = []
        with self.assertRaises(ValueError):
            self.client.import_blocks_from_course('foobar', lambda *_: None)

    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.create_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.get_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.get_library_block_static_asset_files')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.publish_changes')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.set_library_block_olx')
    def test_import_blocks_from_course_on_block_with_olx(
            self,
            mock_set_library_block_olx,
            mock_publish_changes,
            mock_get_library_block_static_asset_files,
            mock_get_library_block,
            mock_create_library_block,
    ):
        """
        Given a course with one block
        When called
        Then extract OLX, write to library and publish.
        """

        usage_key_str = 'lb:foo:bar:foobar:1234'
        library_key_str = 'lib:foo:bar'

        self.client.get_export_keys = mock.MagicMock(return_value=[UsageKey.from_string(usage_key_str)])
        self.client.get_block_data = mock.MagicMock(return_value={'olx': 'fake-olx'})

        mock_create_library_block.side_effect = api.LibraryBlockAlreadyExists
        self.mock_library.library_key = LibraryLocatorV2.from_string(library_key_str)

        self.client.import_blocks_from_course('foobar', lambda *_: None)

        mock_get_library_block.assert_called_once()
        mock_get_library_block_static_asset_files.called_once()
        mock_set_library_block_olx.assert_called_once_with(
            mock.ANY, 'fake-olx')
        mock_publish_changes.assert_called_once()

    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.create_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.get_library_block_static_asset_files')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.set_library_block_olx')
    def test_import_block_when_called_twice_same_block_but_different_course(
            self,
            mock_set_library_block_olx,
            mock_get_library_block_static_asset_files,
            mock_create_library_block,
    ):
        """
        Given an block used by one course
        And another block with same id use by a different course
        And import_block() was called on the first block
        When import_block() is called on the second block
        Then create a library block for the second block
        """
        course_key_str = 'block-v1:FakeCourse+FakeOrg+FakeRun+type@a-fake-block-type+block@fake-block-id'

        modulestore_usage_key = UsageKey.from_string(course_key_str)
        expected_course_key_hash = base64.b32encode(
            hashlib.blake2s(
                str(modulestore_usage_key.course_key).encode()
            ).digest()
        )[:16].decode().lower()
        expected_usage_id = f"{modulestore_usage_key.block_id}_c{expected_course_key_hash}"

        self.client.get_block_data = mock.MagicMock()
        self.client.import_block(modulestore_usage_key)

        mock_create_library_block.assert_called_with(
            self.client.library.library_key,
            modulestore_usage_key.block_type,
            expected_usage_id)
        mock_get_library_block_static_asset_files.assert_called_once()
        mock_set_library_block_olx.assert_called_once()


@mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.OAuthAPIClient')
class EdxApiImportClientTest(TestCase):
    """
    Tests for EdxApiImportClient.
    """

    LMS_URL = 'https://foobar_lms.example.com/'

    STUDIO_URL = 'https://foobar_studio.example.com/'

    library_key_str = 'lib:foobar_content:foobar_library'

    course_key_str = 'course-v1:AFakeCourse+FooBar+1'

    def create_mock_library(self, *, course_id=None, course_key_str=None):
        """
        Create a library mock.
        """
        mock_library = mock.MagicMock()
        mock_library.library_key = LibraryLocatorV2.from_string(
            self.library_key_str
        )
        if course_key_str is None:
            course_key_str = self.course_key_str
        if course_id is None:
            course_id = CourseKey.from_string(course_key_str)
        type(mock_library).course_id = mock.PropertyMock(return_value=course_id)
        return mock_library

    def create_client(self, *, mock_library=None):
        """
        Create a edX API import client mock.
        """
        return api.EdxApiImportClient(
            self.LMS_URL,
            self.STUDIO_URL,
            'foobar_oauth_key',
            'foobar_oauth_secret',
            library=(mock_library or self.create_mock_library()),
        )

    def mock_oauth_client_response(self, mock_oauth_client, *, content=None, exception=None):
        """
        Setup a mock response for oauth client GET calls.
        """
        mock_response = mock.MagicMock()
        mock_content = None
        if exception:
            mock_response.raise_for_status.side_effect = exception
        if content:
            mock_content = mock.PropertyMock(return_value='foobar_file_content')
            type(mock_response).content = mock_content
        mock_oauth_client.get.return_value = mock_response
        if mock_content:
            return mock_response, mock_content
        return mock_response

    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.add_library_block_static_asset_file')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.create_library_block')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.get_library_block_static_asset_files')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.publish_changes')
    @mock.patch('openedx.core.djangoapps.content_libraries.api.courseware_import.set_library_block_olx')
    def test_import_block_when_url_is_from_studio(
            self,
            mock_set_library_block_olx,
            mock_publish_changes,
            mock_get_library_block_static_asset_files,
            mock_create_library_block,
            mock_add_library_block_static_asset_file,
            mock_oauth_client_class,
    ):
        """
        Given an block with one asset provided by a studio.
        When import_block() is called on the block.
        Then a GET to the API endpoint is.
        """

        # Setup mocks.

        static_filename = 'foobar_filename'
        static_content = 'foobar_file_content'
        block_olx = 'foobar-olx'
        usage_key = UsageKey.from_string('lb:foo:bar:foobar:1234')
        # We ensure ``export-file`` belongs to the URL.
        asset_studio_url = f"{self.STUDIO_URL}/foo/bar/export-file/foo/bar"
        block_data = {
            'olx': block_olx,
            'static_files': {static_filename: {'url': asset_studio_url}}
        }
        _, mock_content = self.mock_oauth_client_response(
            mock_oauth_client_class.return_value,
            content=static_content,
        )
        mock_create_library_block.return_value.usage_key = usage_key

        # Create client and call.

        client = self.create_client()
        client.get_block_data = mock.MagicMock(return_value=block_data)
        client.import_block(usage_key)

        # Assertions.

        client.get_block_data.assert_called_once_with(usage_key)
        mock_create_library_block.assert_called_once()
        mock_get_library_block_static_asset_files.assert_called_once()
        mock_content.assert_called()
        mock_add_library_block_static_asset_file.assert_called_once_with(
            usage_key,
            static_filename,
            static_content
        )
        mock_set_library_block_olx.assert_called_once_with(
            usage_key,
            block_olx
        )
        mock_publish_changes.assert_not_called()


class ContentLibraryCollectionsTest(ContentLibrariesRestApiTest):
    """
    Tests for Content Library API collections methods.

    Same guidelines as ContentLibrariesTestCase.
    """

    def setUp(self):
        super().setUp()

        # Create Content Libraries
        self._create_library("test-lib-col-1", "Test Library 1")
        self._create_library("test-lib-col-2", "Test Library 2")

        # Fetch the created ContentLibrare objects so we can access their learning_package.id
        self.lib1 = ContentLibrary.objects.get(slug="test-lib-col-1")
        self.lib2 = ContentLibrary.objects.get(slug="test-lib-col-2")

        # Create Content Library Collections
        self.col1 = api.create_library_collection(
            self.lib1.library_key,
            collection_key="COL1",
            title="Collection 1",
            description="Description for Collection 1",
            created_by=self.user.id,
        )
        self.col2 = api.create_library_collection(
            self.lib2.library_key,
            collection_key="COL2",
            title="Collection 2",
            description="Description for Collection 2",
            created_by=self.user.id,
        )
        self.col3 = api.create_library_collection(
            self.lib2.library_key,
            collection_key="COL3",
            title="Collection 3",
            description="Description for Collection 3",
            created_by=self.user.id,
        )

        # Create some library blocks in lib1
        self.lib1_problem_block = self._add_block_to_library(
            self.lib1.library_key, "problem", "problem1",
        )
        self.lib1_html_block = self._add_block_to_library(
            self.lib1.library_key, "html", "html1",
        )
        # Create a container in lib1
        self.unit1 = self._create_container(
            str(self.lib1.library_key),
            "unit", 'unit-1', 'Unit 1'
        )

        # Create some library blocks in lib2
        self.lib2_problem_block = self._add_block_to_library(
            self.lib2.library_key, "problem", "problem2",
        )

    def test_create_library_collection(self):
        event_receiver = mock.Mock()
        LIBRARY_COLLECTION_CREATED.connect(event_receiver)

        collection = api.create_library_collection(
            self.lib2.library_key,
            collection_key="COL4",
            title="Collection 4",
            description="Description for Collection 4",
            created_by=self.user.id,
        )
        assert collection.key == "COL4"
        assert collection.title == "Collection 4"
        assert collection.description == "Description for Collection 4"
        assert collection.created_by == self.user

        assert event_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_CREATED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib2.library_key,
                        collection_key="COL4",
                    ),
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )

    def test_create_library_collection_invalid_library(self):
        library_key = LibraryLocatorV2.from_string("lib:INVALID:test-lib-does-not-exist")
        with self.assertRaises(api.ContentLibraryNotFound) as exc:
            api.create_library_collection(
                library_key,
                collection_key="COL4",
                title="Collection 3",
            )

    def test_update_library_collection(self):
        event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(event_receiver)

        self.col1 = api.update_library_collection(
            self.lib1.library_key,
            self.col1.key,
            title="New title for Collection 1",
        )
        assert self.col1.key == "COL1"
        assert self.col1.title == "New title for Collection 1"
        assert self.col1.description == "Description for Collection 1"
        assert self.col1.created_by == self.user

        assert event_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_UPDATED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib1.library_key,
                        collection_key="COL1",
                    ),
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )

    def test_update_library_collection_wrong_library(self):
        with self.assertRaises(api.ContentLibraryCollectionNotFound) as exc:
            api.update_library_collection(
                self.lib1.library_key,
                self.col2.key,
            )

    def test_delete_library_collection(self):
        event_receiver = mock.Mock()
        LIBRARY_COLLECTION_DELETED.connect(event_receiver)

        authoring_api.delete_collection(
            self.lib1.learning_package_id,
            self.col1.key,
            hard_delete=True,
        )

        assert event_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_DELETED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib1.library_key,
                        collection_key="COL1",
                    ),
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )

    def test_update_library_collection_items(self):
        assert not list(self.col1.entities.all())

        self.col1 = api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_problem_block["id"]),
                UsageKey.from_string(self.lib1_html_block["id"]),
                LibraryContainerLocator.from_string(self.unit1["id"]),
            ],
        )
        assert len(self.col1.entities.all()) == 3

        self.col1 = api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_html_block["id"]),
            ],
            remove=True,
        )
        assert len(self.col1.entities.all()) == 2

    def test_update_library_collection_components_event(self):
        """
        Check that a CONTENT_OBJECT_ASSOCIATIONS_CHANGED event is raised for each added/removed component.
        """
        event_receiver = mock.Mock()
        CONTENT_OBJECT_ASSOCIATIONS_CHANGED.connect(event_receiver)
        LIBRARY_COLLECTION_UPDATED.connect(event_receiver)

        api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_problem_block["id"]),
                UsageKey.from_string(self.lib1_html_block["id"]),
                LibraryContainerLocator.from_string(self.unit1["id"]),
            ],
        )

        assert event_receiver.call_count == 4
        self.assertDictContainsSubset(
            {
                "signal": CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
                "sender": None,
                "content_object": ContentObjectChangedData(
                    object_id=self.lib1_problem_block["id"],
                    changes=["collections"],
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )
        self.assertDictContainsSubset(
            {
                "signal": CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
                "sender": None,
                "content_object": ContentObjectChangedData(
                    object_id=self.lib1_html_block["id"],
                    changes=["collections"],
                ),
            },
            event_receiver.call_args_list[1].kwargs,
        )
        self.assertDictContainsSubset(
            {
                "signal": CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
                "sender": None,
                "content_object": ContentObjectChangedData(
                    object_id=self.unit1["id"],
                    changes=["collections"],
                ),
            },
            event_receiver.call_args_list[2].kwargs,
        )
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_UPDATED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib1.library_key,
                        collection_key="COL1",
                    ),
                ),
            },
            event_receiver.call_args_list[3].kwargs,
        )

    def test_update_collection_components_from_wrong_library(self):
        with self.assertRaises(api.ContentLibraryBlockNotFound) as exc:
            api.update_library_collection_items(
                self.lib2.library_key,
                self.col2.key,
                opaque_keys=[
                    UsageKey.from_string(self.lib1_problem_block["id"]),
                    UsageKey.from_string(self.lib1_html_block["id"]),
                    LibraryContainerLocator.from_string(self.unit1["id"]),
                ],
            )
            assert self.lib1_problem_block["id"] in str(exc.exception)

    def test_set_library_component_collections(self):
        event_receiver = mock.Mock()
        CONTENT_OBJECT_ASSOCIATIONS_CHANGED.connect(event_receiver)
        collection_update_event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(collection_update_event_receiver)
        assert not list(self.col2.entities.all())
        component = api.get_component_from_usage_key(UsageKey.from_string(self.lib2_problem_block["id"]))
        api.set_library_item_collections(
            library_key=self.lib2.library_key,
            entity_key=component.publishable_entity.key,
            collection_keys=[self.col2.key, self.col3.key],
        )

        assert len(authoring_api.get_collection(self.lib2.learning_package_id, self.col2.key).entities.all()) == 1
        assert len(authoring_api.get_collection(self.lib2.learning_package_id, self.col3.key).entities.all()) == 1
        assert {
            "signal": CONTENT_OBJECT_ASSOCIATIONS_CHANGED,
            "sender": None,
            "content_object": ContentObjectChangedData(
                object_id=self.lib2_problem_block["id"],
                changes=["collections"],
            ),
        }.items() <= event_receiver.call_args_list[0].kwargs.items()

        assert len(collection_update_event_receiver.call_args_list) == 2
        collection_update_events = [call.kwargs for call in collection_update_event_receiver.call_args_list]
        assert all(event["signal"] == LIBRARY_COLLECTION_UPDATED for event in collection_update_events)
        assert {event["library_collection"] for event in collection_update_events} == {
            LibraryCollectionData(
                collection_key=api.library_collection_locator(self.lib2.library_key, collection_key=self.col2.key),
                background=True,
            ),
            LibraryCollectionData(
                collection_key=api.library_collection_locator(self.lib2.library_key, collection_key=self.col3.key),
                background=True,
            )
        }

    def test_delete_library_block(self):
        api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_problem_block["id"]),
                UsageKey.from_string(self.lib1_html_block["id"]),
            ],
        )

        event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(event_receiver)

        api.delete_library_block(UsageKey.from_string(self.lib1_problem_block["id"]))

        assert event_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_UPDATED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib1.library_key,
                        collection_key=self.col1.key,
                    ),
                    background=True,
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )

    def test_delete_library_container(self):
        api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_problem_block["id"]),
                UsageKey.from_string(self.lib1_html_block["id"]),
                LibraryContainerLocator.from_string(self.unit1["id"]),
            ],
        )

        event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(event_receiver)

        api.delete_container(LibraryContainerLocator.from_string(self.unit1["id"]))

        assert event_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_UPDATED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib1.library_key,
                        collection_key=self.col1.key,
                    ),
                    background=True,
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )

    def test_restore_library_block(self):
        api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_problem_block["id"]),
                UsageKey.from_string(self.lib1_html_block["id"]),
            ],
        )

        event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(event_receiver)

        api.restore_library_block(UsageKey.from_string(self.lib1_problem_block["id"]))

        assert event_receiver.call_count == 1
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_COLLECTION_UPDATED,
                "sender": None,
                "library_collection": LibraryCollectionData(
                    collection_key=api.library_collection_locator(
                        self.lib1.library_key,
                        collection_key=self.col1.key,
                    ),
                    background=True,
                ),
            },
            event_receiver.call_args_list[0].kwargs,
        )

    def test_add_component_and_revert(self):
        # Publish changes
        api.publish_changes(self.lib1.library_key)

        # Create a new component that will only exist as a draft
        new_problem_block = self._add_block_to_library(
            self.lib1.library_key, "problem", "problemNEW",
        )

        # Add component. Note: collections are not part of the draft/publish cycle so this is not a draft change.
        api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_html_block["id"]),
                UsageKey.from_string(new_problem_block["id"]),
            ],
        )

        collection_update_event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(collection_update_event_receiver)

        api.revert_changes(self.lib1.library_key)

        assert collection_update_event_receiver.call_count == 1
        assert {
            "signal": LIBRARY_COLLECTION_UPDATED,
            "sender": None,
            "library_collection": LibraryCollectionData(
                collection_key=api.library_collection_locator(
                    self.lib1.library_key,
                    collection_key=self.col1.key,
                ),
            ),
        }.items() <= collection_update_event_receiver.call_args_list[0].kwargs.items()

    def test_delete_component_and_revert(self):
        """
        When a component is deleted and then the delete is reverted, signals
        will be emitted to update any containing collections.
        """
        # Add components and publish
        api.update_library_collection_items(
            self.lib1.library_key,
            self.col1.key,
            opaque_keys=[
                UsageKey.from_string(self.lib1_problem_block["id"]),
                UsageKey.from_string(self.lib1_html_block["id"])
            ],
        )
        api.publish_changes(self.lib1.library_key)

        # Delete component and revert
        api.delete_library_block(UsageKey.from_string(self.lib1_problem_block["id"]))

        collection_update_event_receiver = mock.Mock()
        LIBRARY_COLLECTION_UPDATED.connect(collection_update_event_receiver)

        api.revert_changes(self.lib1.library_key)

        assert collection_update_event_receiver.call_count == 1
        assert {
            "signal": LIBRARY_COLLECTION_UPDATED,
            "sender": None,
            "library_collection": LibraryCollectionData(
                collection_key=api.library_collection_locator(
                    self.lib1.library_key,
                    collection_key=self.col1.key,
                ),
            ),
        }.items() <= collection_update_event_receiver.call_args_list[0].kwargs.items()


class ContentLibraryContainersTest(ContentLibrariesRestApiTest):
    """
    Tests for Content Library API containers methods.
    """

    def setUp(self):
        super().setUp()

        # Create Content Libraries
        self._create_library("test-lib-cont-1", "Test Library 1")

        # Fetch the created ContentLibrare objects so we can access their learning_package.id
        self.lib1 = ContentLibrary.objects.get(slug="test-lib-cont-1")

        # Create Units
        self.unit1 = api.create_container(self.lib1.library_key, api.ContainerType.Unit, 'unit-1', 'Unit 1', None)
        self.unit2 = api.create_container(self.lib1.library_key, api.ContainerType.Unit, 'unit-2', 'Unit 2', None)

        # Create XBlocks
        # Create some library blocks in lib1
        self.problem_block = self._add_block_to_library(
            self.lib1.library_key, "problem", "problem1",
        )
        self.problem_block_usage_key = UsageKey.from_string(self.problem_block["id"])
        self.html_block = self._add_block_to_library(
            self.lib1.library_key, "html", "html1",
        )
        self.html_block_usage_key = UsageKey.from_string(self.html_block["id"])

        # Add content to units
        api.update_container_children(
            self.unit1.container_key,
            [self.problem_block_usage_key, self.html_block_usage_key],
            None,
        )
        api.update_container_children(
            self.unit2.container_key,
            [self.html_block_usage_key],
            None,
        )

    def test_get_containers_contains_component(self):
        problem_block_containers = api.get_containers_contains_component(self.problem_block_usage_key)
        html_block_containers = api.get_containers_contains_component(self.html_block_usage_key)

        assert len(problem_block_containers) == 1
        assert problem_block_containers[0].container_key == self.unit1.container_key

        assert len(html_block_containers) == 2
        assert html_block_containers[0].container_key == self.unit1.container_key
        assert html_block_containers[1].container_key == self.unit2.container_key

    def _validate_calls_of_html_block(self, event_mock):
        """
        Validate that the `event_mock` has been called twice
        using the `LIBRARY_CONTAINER_UPDATED` signal.
        """
        assert event_mock.call_count == 2
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_UPDATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    container_key=self.unit1.container_key,
                    background=True,
                )
            },
            event_mock.call_args_list[0].kwargs,
        )
        self.assertDictContainsSubset(
            {
                "signal": LIBRARY_CONTAINER_UPDATED,
                "sender": None,
                "library_container": LibraryContainerData(
                    container_key=self.unit2.container_key,
                    background=True,
                )
            },
            event_mock.call_args_list[1].kwargs,
        )

    def test_call_container_update_signal_when_delete_component(self):
        container_update_event_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(container_update_event_receiver)

        api.delete_library_block(self.html_block_usage_key)
        self._validate_calls_of_html_block(container_update_event_receiver)

    def test_call_container_update_signal_when_restore_component(self):
        api.delete_library_block(self.html_block_usage_key)

        container_update_event_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(container_update_event_receiver)
        api.restore_library_block(self.html_block_usage_key)

        self._validate_calls_of_html_block(container_update_event_receiver)

    def test_call_container_update_signal_when_update_olx(self):
        block_olx = "<html><b>Hello world!</b></html>"
        container_update_event_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(container_update_event_receiver)

        self._set_library_block_olx(self.html_block_usage_key, block_olx)
        self._validate_calls_of_html_block(container_update_event_receiver)

    def test_call_container_update_signal_when_update_component(self):
        block_olx = "<html><b>Hello world!</b></html>"
        container_update_event_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(container_update_event_receiver)

        self._set_library_block_fields(self.html_block_usage_key, {"data": block_olx, "metadata": {}})
        self._validate_calls_of_html_block(container_update_event_receiver)

    def test_delete_component_and_revert(self):
        """
        When a component is deleted and then the delete is reverted, signals
        will be emitted to update any containing containers.
        """
        # Add components and publish
        api.update_container_children(self.unit1.container_key, [
            UsageKey.from_string(self.problem_block["id"]),
        ], user_id=None)
        api.publish_changes(self.lib1.library_key)

        # Delete component and revert
        api.delete_library_block(UsageKey.from_string(self.problem_block["id"]))

        container_event_receiver = mock.Mock()
        LIBRARY_CONTAINER_UPDATED.connect(container_event_receiver)

        api.revert_changes(self.lib1.library_key)

        assert container_event_receiver.call_count == 1
        assert {
            "signal": LIBRARY_CONTAINER_UPDATED,
            "sender": None,
            "library_container": LibraryContainerData(container_key=self.unit1.container_key),
        }.items() <= container_event_receiver.call_args_list[0].kwargs.items()
