"""
Tests for Learning-Core-based Content Libraries
"""
from opaque_keys.edx.locator import LibraryContainerLocator, LibraryLocatorV2, LibraryUsageLocatorV2
from openedx_events.content_authoring.signals import (
    ContentLibraryData,
    LibraryBlockData,
    LibraryCollectionData,
    LibraryContainerData,
    CONTENT_LIBRARY_CREATED,
    CONTENT_LIBRARY_DELETED,
    CONTENT_LIBRARY_UPDATED,
    LIBRARY_BLOCK_CREATED,
    LIBRARY_BLOCK_DELETED,
    LIBRARY_BLOCK_UPDATED,
    LIBRARY_BLOCK_PUBLISHED,
    LIBRARY_COLLECTION_CREATED,
    LIBRARY_COLLECTION_DELETED,
    LIBRARY_COLLECTION_UPDATED,
    LIBRARY_CONTAINER_CREATED,
    LIBRARY_CONTAINER_DELETED,
    LIBRARY_CONTAINER_UPDATED,
    LIBRARY_CONTAINER_PUBLISHED,
)
from openedx_events.tests.utils import OpenEdxEventsTestMixin

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from openedx.core.djangolib.testing.utils import skip_unless_cms


@skip_unless_cms
class ContentLibrariesEventsTestCase(ContentLibrariesRestApiTest, OpenEdxEventsTestMixin):
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
        LIBRARY_BLOCK_PUBLISHED,
        LIBRARY_COLLECTION_CREATED,
        LIBRARY_COLLECTION_DELETED,
        LIBRARY_COLLECTION_UPDATED,
        LIBRARY_CONTAINER_CREATED,
        LIBRARY_CONTAINER_DELETED,
        LIBRARY_CONTAINER_UPDATED,
        LIBRARY_CONTAINER_PUBLISHED,
    ]
    ENABLED_OPENEDX_EVENTS = [e.event_type for e in ALL_EVENTS]

    @classmethod
    def setUpClass(cls):
        """
        Set up class method for the Test class.

        TODO: It's unclear why we need to call start_events_isolation ourselves rather than relying on
              OpenEdxEventsTestMixin.setUpClass to handle it. It fails in a *flaky/inconsistent fasion* if we don't,
              and many other test cases do it, so we're following a pattern here.
              But that pattern doesn't really make sense.
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

    ############################## Libraries ##################################

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

    ############################## Components (XBlocks) ##################################

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
            "signal": LIBRARY_BLOCK_PUBLISHED,
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

    ############################## Containers ##################################

    def test_unit_crud(self):
        """
        Test Create, Read, Update, and Delete of a Unit
        """
        # Create a unit:
        container_data = self._create_container(self.lib1_key, "unit", slug="u1", display_name="Test Unit")
        container_key = LibraryContainerLocator.from_string(container_data["id"])

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_CREATED,
            "library_container": LibraryContainerData(container_key),
        })

        # Update the unit:
        self._update_container(container_key, display_name="Unit ABC")

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_UPDATED,
            "library_container": LibraryContainerData(container_key),
        })

        # Delete the unit
        self._delete_container(container_key)
        self._get_container(container_key, expect_response=404)
        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_DELETED,
            "library_container": LibraryContainerData(container_key),
        })

    def test_publish_container(self):
        """
        Test that we can publish the changes to a specific container
        """
        # Create two containers and add some components
        container1 = self._create_container(self.lib1_key, "unit", display_name="Alpha Unit", slug=None)
        container2 = self._create_container(self.lib1_key, "unit", display_name="Bravo Unit", slug=None)
        problem_block = self._add_block_to_library(self.lib1_key, "problem", "Problem1", can_stand_alone=False)
        html_block = self._add_block_to_library(self.lib1_key, "html", "Html1", can_stand_alone=False)
        html_block2 = self._add_block_to_library(self.lib1_key, "html", "Html2", can_stand_alone=False)
        self._add_container_components(container1["id"], children_ids=[problem_block["id"], html_block["id"]])
        self._add_container_components(container2["id"], children_ids=[html_block["id"], html_block2["id"]])
        # At first everything is unpublished:
        c1_before = self._get_container(container1["id"])
        assert c1_before["has_unpublished_changes"]
        c2_before = self._get_container(container2["id"])
        assert c2_before["has_unpublished_changes"]

        # clear event log after the initial mock data setup is complete:
        self.clear_events()

        # Now publish only Container 1
        self._publish_container(container1["id"])

        # Now it is published:
        c1_after = self._get_container(container1["id"])
        assert c1_after["has_unpublished_changes"] is False
        # And publish events were emitted:
        self.expect_new_events(
            {  # An event for container 1 being published:
                "signal": LIBRARY_CONTAINER_PUBLISHED,
                "library_container": LibraryContainerData(
                    container_key=LibraryContainerLocator.from_string(container1["id"]),
                ),
            },
            {  # An event for the problem block in container 1:
                "signal": LIBRARY_BLOCK_PUBLISHED,
                "library_block": LibraryBlockData(
                    self.lib1_key, LibraryUsageLocatorV2.from_string(problem_block["id"]),
                ),
            },
            {  # An event for the html block in container 1 (and container 2):
                "signal": LIBRARY_BLOCK_PUBLISHED,
                "library_block": LibraryBlockData(
                    self.lib1_key, LibraryUsageLocatorV2.from_string(html_block["id"]),
                ),
            },
        )

        # and container 2 is still unpublished
        c2_after = self._get_container(container2["id"])
        assert c2_after["has_unpublished_changes"]

    def test_restore_unit(self):
        """
        Test restoring a deleted unit via the "restore" API.
        """
        # Create a unit:
        container_data = self._create_container(self.lib1_key, "unit", slug="u1", display_name="Test Unit")
        container_key=LibraryContainerLocator.from_string(container_data["id"])

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_CREATED,
            "library_container": LibraryContainerData(container_key),
        })

        # Delete the unit
        self._delete_container(container_data["id"])

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_DELETED,
            "library_container": LibraryContainerData(container_key),
        })

        # Restore the unit
        self._restore_container(container_data["id"])

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_CREATED,
            "library_container": LibraryContainerData(container_key),
        })

    def test_restore_unit_via_revert(self):
        """
        Test restoring a deleted unit by reverting changes.
        """
        # Publish the existing setup and clear events
        self._commit_library_changes(self.lib1_key)
        self.clear_events()

        # Create a unit:
        container_data = self._create_container(self.lib1_key, "unit", slug="u1", display_name="Test Unit")
        container_key=LibraryContainerLocator.from_string(container_data["id"])

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_CREATED,
            "library_container": LibraryContainerData(container_key),
        })

        # Publish changes
        self._publish_container(container_key)
        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_PUBLISHED,
            "library_container": LibraryContainerData(container_key),
        })

        # Delete the unit
        self._delete_container(container_data["id"])

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_DELETED,
            "library_container": LibraryContainerData(container_key),
        })

        # Revert changes, which will re-create the unit:
        self._revert_library_changes(self.lib1_key)

        self.expect_new_events({
            "signal": LIBRARY_CONTAINER_CREATED,
            "library_container": LibraryContainerData(container_key),
        })
