"""
Tests for in-course reverification user partition creation.

This should really belong to the verify_student app,
but we can't move it there because it's in the LMS and we're
currently applying these rules on publish from Studio.

In the future, this functionality should be a course transformation
defined in the verify_student app, and these tests should be moved
into verify_student.

"""

from mock import patch

from django.conf import settings

from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.partition_schemes import VerificationPartitionScheme
from openedx.core.djangoapps.credit.verification_access import update_verification_partitions
from openedx.core.djangoapps.credit.signals import on_pre_publish
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls_range
from xmodule.partitions.partitions import Group, UserPartition


class CreateVerificationPartitionTest(ModuleStoreTestCase):
    """
    Tests for applying verification access rules.
    """

    # Run the tests in split modulestore
    # While verification access will work in old-Mongo, it's not something
    # we're committed to supporting, since this feature is meant for use
    # in new courses.
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @patch.dict(settings.FEATURES, {"ENABLE_COURSEWARE_INDEX": False})
    def setUp(self):
        super(CreateVerificationPartitionTest, self).setUp()

        # Disconnect the signal receiver -- we'll invoke the update code ourselves
        SignalHandler.pre_publish.disconnect(receiver=on_pre_publish)
        self.addCleanup(SignalHandler.pre_publish.connect, receiver=on_pre_publish)

        # Create a dummy course with a single verification checkpoint
        # Because we need to check "exam" content surrounding the ICRV checkpoint,
        # we need to create a fairly large course structure, with multiple sections,
        # subsections, verticals, units, and items.
        self.course = CourseFactory()
        self.sections = [
            ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section A'),
            ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section B'),
        ]
        self.subsections = [
            ItemFactory.create(parent=self.sections[0], category='sequential', display_name='Test Subsection A 1'),
            ItemFactory.create(parent=self.sections[0], category='sequential', display_name='Test Subsection A 2'),
            ItemFactory.create(parent=self.sections[1], category='sequential', display_name='Test Subsection B 1'),
            ItemFactory.create(parent=self.sections[1], category='sequential', display_name='Test Subsection B 2'),
        ]
        self.verticals = [
            ItemFactory.create(parent=self.subsections[0], category='vertical', display_name='Test Unit A 1 a'),
            ItemFactory.create(parent=self.subsections[0], category='vertical', display_name='Test Unit A 1 b'),
            ItemFactory.create(parent=self.subsections[1], category='vertical', display_name='Test Unit A 2 a'),
            ItemFactory.create(parent=self.subsections[1], category='vertical', display_name='Test Unit A 2 b'),
            ItemFactory.create(parent=self.subsections[2], category='vertical', display_name='Test Unit B 1 a'),
            ItemFactory.create(parent=self.subsections[2], category='vertical', display_name='Test Unit B 1 b'),
            ItemFactory.create(parent=self.subsections[3], category='vertical', display_name='Test Unit B 2 a'),
            ItemFactory.create(parent=self.subsections[3], category='vertical', display_name='Test Unit B 2 b'),
        ]
        self.icrv = ItemFactory.create(parent=self.verticals[0], category='edx-reverification-block')
        self.sibling_problem = ItemFactory.create(parent=self.verticals[0], category='problem')

    def test_creates_user_partitions(self):
        self._update_partitions()

        # Check that a new user partition was created for the ICRV block
        self.assertEqual(len(self.course.user_partitions), 1)
        partition = self.course.user_partitions[0]
        self.assertEqual(partition.scheme.name, "verification")
        self.assertEqual(partition.parameters["location"], unicode(self.icrv.location))

        # Check that the groups for the partition were created correctly
        self.assertEqual(len(partition.groups), 2)
        self.assertItemsEqual(
            [g.id for g in partition.groups],
            [
                VerificationPartitionScheme.ALLOW,
                VerificationPartitionScheme.DENY,
            ]
        )

    @patch.dict(settings.FEATURES, {"ENABLE_COURSEWARE_INDEX": False})
    def test_removes_deleted_user_partitions(self):
        self._update_partitions()

        # Delete the reverification block, then update the partitions
        self.store.delete_item(
            self.icrv.location,
            ModuleStoreEnum.UserID.test,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self._update_partitions()

        # Check that the user partition was marked as inactive
        self.assertEqual(len(self.course.user_partitions), 1)
        partition = self.course.user_partitions[0]
        self.assertFalse(partition.active)
        self.assertEqual(partition.scheme.name, "verification")

    @patch.dict(settings.FEATURES, {"ENABLE_COURSEWARE_INDEX": False})
    def test_preserves_partition_id_for_verified_partitions(self):
        self._update_partitions()
        partition_id = self.course.user_partitions[0].id
        self._update_partitions()
        new_partition_id = self.course.user_partitions[0].id
        self.assertEqual(partition_id, new_partition_id)

    @patch.dict(settings.FEATURES, {"ENABLE_COURSEWARE_INDEX": False})
    def test_preserves_existing_user_partitions(self):
        # Add other, non-verified partition to the course
        self.course.user_partitions = [
            UserPartition(
                id=0,
                name='Cohort user partition',
                scheme=UserPartition.get_scheme('cohort'),
                description='Cohorted user partition',
                groups=[
                    Group(id=0, name="Group A"),
                    Group(id=1, name="Group B"),
                ],
            ),
            UserPartition(
                id=1,
                name='Random user partition',
                scheme=UserPartition.get_scheme('random'),
                description='Random user partition',
                groups=[
                    Group(id=0, name="Group A"),
                    Group(id=1, name="Group B"),
                ],
            ),
        ]
        self.course = self.store.update_item(self.course, ModuleStoreEnum.UserID.test)

        # Update the verification partitions.
        # The existing partitions should still be available
        self._update_partitions()
        partition_ids = [p.id for p in self.course.user_partitions]
        self.assertEqual(len(partition_ids), 3)
        self.assertIn(0, partition_ids)
        self.assertIn(1, partition_ids)

    def test_multiple_reverification_blocks(self):
        # Add an additional ICRV block in another section
        other_icrv = ItemFactory.create(parent=self.verticals[3], category='edx-reverification-block')
        self._update_partitions()

        # Expect that both ICRV blocks have corresponding partitions
        self.assertEqual(len(self.course.user_partitions), 2)
        partition_locations = [p.parameters.get("location") for p in self.course.user_partitions]
        self.assertIn(unicode(self.icrv.location), partition_locations)
        self.assertIn(unicode(other_icrv.location), partition_locations)

        # Delete the first ICRV block and update partitions
        icrv_location = self.icrv.location
        self.store.delete_item(
            self.icrv.location,
            ModuleStoreEnum.UserID.test,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )
        self._update_partitions()

        # Expect that the correct partition is marked as inactive
        self.assertEqual(len(self.course.user_partitions), 2)
        partitions_by_loc = {
            p.parameters["location"]: p
            for p in self.course.user_partitions
        }
        self.assertFalse(partitions_by_loc[unicode(icrv_location)].active)
        self.assertTrue(partitions_by_loc[unicode(other_icrv.location)].active)

    def test_query_counts_with_no_reverification_blocks(self):
        # Delete the ICRV block, so the number of ICRV blocks is zero
        self.store.delete_item(
            self.icrv.location,
            ModuleStoreEnum.UserID.test,
            revision=ModuleStoreEnum.RevisionOption.published_only
        )

        # 2 calls: get the course (definitions + structures)
        # 2 calls: look up ICRV blocks in the course (definitions + structures)
        with check_mongo_calls_range(max_finds=4, max_sends=2):
            self._update_partitions(reload_items=False)

    def test_query_counts_with_one_reverification_block(self):
        # One ICRV block created in the setup method
        # Additional call to load the ICRV block
        with check_mongo_calls_range(max_finds=5, max_sends=3):
            self._update_partitions(reload_items=False)

    def test_query_counts_with_multiple_reverification_blocks(self):
        # Total of two ICRV blocks (one created in setup method)
        # Additional call to load each ICRV block
        ItemFactory.create(parent=self.verticals[3], category='edx-reverification-block')
        with check_mongo_calls_range(max_finds=6, max_sends=3):
            self._update_partitions(reload_items=False)

    def _update_partitions(self, reload_items=True):
        """Update user partitions in the course descriptor, then reload the content. """
        update_verification_partitions(self.course.id)  # pylint: disable=no-member

        # Reload each component so we can see the changes
        if reload_items:
            self.course = self.store.get_course(self.course.id)  # pylint: disable=no-member
            self.sections = [self._reload_item(section.location) for section in self.sections]
            self.subsections = [self._reload_item(subsection.location) for subsection in self.subsections]
            self.verticals = [self._reload_item(vertical.location) for vertical in self.verticals]
            self.icrv = self._reload_item(self.icrv.location)
            self.sibling_problem = self._reload_item(self.sibling_problem.location)

    def _reload_item(self, location):
        """Safely reload an item from the moduelstore. """
        try:
            return self.store.get_item(location)
        except ItemNotFoundError:
            return None


class WriteOnPublishTest(ModuleStoreTestCase):
    """
    Verify that updates to the course descriptor's
    user partitions are written automatically on publish.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @patch.dict(settings.FEATURES, {"ENABLE_COURSEWARE_INDEX": False})
    def setUp(self):
        super(WriteOnPublishTest, self).setUp()

        # Create a dummy course with an ICRV block
        self.course = CourseFactory()
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.subsection = ItemFactory.create(parent=self.section, category='sequential', display_name='Test Subsection')
        self.vertical = ItemFactory.create(parent=self.subsection, category='vertical', display_name='Test Unit')
        self.icrv = ItemFactory.create(parent=self.vertical, category='edx-reverification-block')

        # Mark the course as credit
        CreditCourse.objects.create(course_key=self.course.id, enabled=True)  # pylint: disable=no-member

    @patch.dict(settings.FEATURES, {"ENABLE_COURSEWARE_INDEX": False})
    def test_can_write_on_publish_signal(self):
        # Sanity check -- initially user partitions should be empty
        self.assertEqual(self.course.user_partitions, [])

        # Make and publish a change to a block, which should trigger the publish signal
        with self.store.bulk_operations(self.course.id):  # pylint: disable=no-member
            self.icrv.display_name = "Updated display name"
            self.store.update_item(self.icrv, ModuleStoreEnum.UserID.test)
            self.store.publish(self.icrv.location, ModuleStoreEnum.UserID.test)

        # Within the test, the course pre-publish signal should have fired synchronously
        # Since the course is marked as credit, the in-course verification partitions
        # should have been created.
        # We need to verify that these changes were actually persisted to the modulestore.
        retrieved_course = self.store.get_course(self.course.id)  # pylint: disable=no-member
        self.assertEqual(len(retrieved_course.user_partitions), 1)
