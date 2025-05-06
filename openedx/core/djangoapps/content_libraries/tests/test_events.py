"""
Tests for Learning-Core-based Content Libraries
"""
import ddt
from opaque_keys.edx.locator import LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_events.content_authoring.data import (
    ContentLibraryData,
    LibraryBlockData,
)
from openedx_events.content_authoring.signals import (
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    LIBRARY_BLOCK_UPDATED
)
from openedx_events.tests.utils import OpenEdxEventsTestMixin

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from openedx.core.djangolib.testing.utils import skip_unless_cms


@skip_unless_cms
@ddt.ddt
class ContentLibrariesTestCase(ContentLibrariesRestApiTest, OpenEdxEventsTestMixin):
    """
    General tests for Learning-Core-based Content Libraries

    These tests use the REST API, which in turn relies on the Python API.
    Some tests may use the python API directly if necessary to provide
    coverage of any code paths not accessible via the REST API.

    In general, these tests should
    (1) Use public APIs only - don't directly create data using other methods,
        which results in a less realistic test and ties the test suite too
        closely to specific implementation details.
        (Exception: users can be provisioned using a user factory)
    (2) Assert that fields are present in responses, but don't assert that the
        entire response has some specific shape. That way, things like adding
        new fields to an API response, which are backwards compatible, won't
        break any tests, but backwards-incompatible API changes will.

    WARNING: every test should have a unique library slug, because even though
    the django/mysql database gets reset for each test case, the lookup between
    library slug and bundle UUID does not because it's assumed to be immutable
    and cached forever.
    """
    ALL_EVENTS = [
        CONTENT_LIBRARY_CREATED,
        CONTENT_LIBRARY_DELETED,
        CONTENT_LIBRARY_UPDATED,
        LIBRARY_BLOCK_CREATED,
        LIBRARY_BLOCK_DELETED,
        LIBRARY_BLOCK_UPDATED,
    ]
    ENABLED_OPENEDX_EVENTS = [e.event_type for e in ALL_EVENTS]

    @classmethod
    def setUpClass(cls):
        """
        Set up class method for the Test class.

        TODO: It's unclear why we need to call start_events_isolation ourselves rather than relying on
              OpenEdxEventsTestMixin.setUpClass to handle it. It fails it we don't, and many other test cases do it,
              so we're following a pattern here. But that pattern doesn't really make sense.
        """
        super().setUpClass()
        cls.start_events_isolation()

    def setUp(self):
        super().setUp()

        # Create some useful data:
        self.lib1 = self._create_library(
            slug="test_lib_1",
            title="Library 1",
            description="First Library for testing",
        )
        self.lib1_key = LibraryLocatorV2.from_string(self.lib1['id'])

        # From now on, every time an event is emitted, add it to this set:
        self.new_events: list[dict] = []

        def event_receiver(**kwargs):
            self.new_events.append(kwargs)

        for e in self.ALL_EVENTS:
            e.connect(event_receiver)

        def disconnect_all():
            for e in self.ALL_EVENTS:
                e.disconnect(event_receiver)

        self.addCleanup(disconnect_all)

    def clear_events(self):
        """ Clear the log of events that we've seen so far. """
        self.new_events.clear()

    def expect_new_events(self, *expected_events: list[dict]):
        """
        assert the the specified events have been emitted since the last call to
        this function.
        """
        # We assume the events may not be in order. Assuming a specific order can lead to flaky tests.
        for expected in expected_events:
            found = False
            for i, actual in enumerate(self.new_events):
                if expected.items() <= actual.items():
                    self.new_events.pop(i)
                    found = True
                    break
            if not found:
                raise AssertionError(f"Event {expected} not found among actual events: {self.new_events}")
        if len(self.new_events) > 0:
            raise AssertionError(f"Events were emitted but not expected: {self.new_events}")
        self.clear_events()

    def test_content_library_crud_events(self):
        """
        Check that CONTENT_LIBRARY_CREATED event is sent when a content library is created, updated, and deleted
        """
        # Setup: none
        # Action - create a library
        new_lib = self._create_library(
            slug="new_lib",
            title="New Testing Library",
            description="New Library for testing",
        )
        lib_key = LibraryLocatorV2.from_string(new_lib['id'])

        # Expect a CREATED event:
        self.expect_new_events({
            "signal": CONTENT_LIBRARY_CREATED,
            "content_library": ContentLibraryData(library_key=lib_key),
        })

        # Action - change the library name:
        self._update_library(lib_key=str(lib_key), title="New title")
        # Expect an UPDATED event:
        self.expect_new_events({
            "signal": CONTENT_LIBRARY_UPDATED,
            "content_library": ContentLibraryData(library_key=lib_key),
        })

        # Action - delete the library:
        self._delete_library(str(lib_key))
        # Expect a DELETED event:
        self.expect_new_events({
            "signal": CONTENT_LIBRARY_DELETED,
            "content_library": ContentLibraryData(library_key=lib_key),
        })

    # Should deleting a library send out _DELETED events for all the items in the library too?

    def test_library_block_create_event(self):
        """
        Check that LIBRARY_BLOCK_CREATED event is sent when a library block is created.
        """
        add_result = self._add_block_to_library(self.lib1_key, "problem", "problem1")
        usage_key = LibraryUsageLocatorV2.from_string(add_result["id"])

        self.expect_new_events({
            "signal": LIBRARY_BLOCK_CREATED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

    def test_library_block_update_and_publish_events(self):
        """
        Check that appropriate events are emitted when an existing block is updated.
        """
        # This block should be ignored:
        self._add_block_to_library(self.lib1_key, "problem", "problem1")
        # This block will be used in the tests:
        add_result = self._add_block_to_library(self.lib1_key, "problem", "problem2")
        usage_key = LibraryUsageLocatorV2.from_string(add_result["id"])
        # Clear events from creating the blocks:
        self.clear_events()

        # Now update the block's OLX:
        new_olx = """
        <problem display_name="New Multi Choice Question" max_attempts="5">
            <multiplechoiceresponse>...</multiplechoiceresponse>
        </problem>
        """.strip()
        self._set_library_block_olx(usage_key, new_olx)
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_UPDATED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

        # Now add a static asset file to the block:
        self._set_library_block_asset(usage_key, "static/test.txt", b"data")
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_UPDATED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

        # Then delete the static asset:
        self._delete_library_block_asset(usage_key, 'static/text.txt')
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_UPDATED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

        # Then publish the block:
        self._publish_library_block(usage_key)
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_UPDATED,  # FIXME: this should be a _PUBLISHED event
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

    def test_revert_delete(self):
        """
        Test that when a block is deleted and then the delete is reverted, a
        _CREATED event is sent.
        """
        # This block should be ignored:
        self._add_block_to_library(self.lib1_key, "problem", "problem1")
        # This block will be used in the tests:
        add_result = self._add_block_to_library(self.lib1_key, "problem", "problem2")
        usage_key = LibraryUsageLocatorV2.from_string(add_result["id"])
        # Publish changes
        self._commit_library_changes(self.lib1_key)
        # Clear events from creating the blocks:
        self.clear_events()

        # Delete the block:
        self._delete_library_block(usage_key)
        # That should emit a _DELETED event:
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_DELETED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

        # Revert the change:
        self._revert_library_changes(self.lib1_key)
        # That should result in a _CREATED event:
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_CREATED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

    def test_revert_create(self):
        """
        Test that when a block is created and then the changes are reverted, a
        _DELETED event is sent.
        """
        # Publish any changes from setUp()
        self._commit_library_changes(self.lib1_key)
        # Clear events:
        self.clear_events()

        # Create the block:
        add_result = self._add_block_to_library(self.lib1_key, "problem", "problem2")
        usage_key = LibraryUsageLocatorV2.from_string(add_result["id"])
        # That should result in a _CREATED event:
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_CREATED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })

        # Revert the change:
        self._revert_library_changes(self.lib1_key)
        # That should result in a _DELETED event:
        self.expect_new_events({
            "signal": LIBRARY_BLOCK_DELETED,
            "library_block": LibraryBlockData(self.lib1_key, usage_key),
        })
