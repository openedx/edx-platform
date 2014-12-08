"""
Tests of the LMS XBlock Mixin
"""
import ddt
from django.conf import settings

from xblock.validation import ValidationMessage
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.modulestore_settings import update_module_store_settings
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.partitions.partitions import Group, UserPartition


class LmsXBlockMixinTestCase(ModuleStoreTestCase):
    """
    Base class for XBlock mixin tests cases. A simple course with a single user partition is created
    in setUp for all subclasses to use.
    """
    def build_course(self):
        """
        Build up a course tree with a UserPartition.
        """
        # pylint: disable=attribute-defined-outside-init
        self.user_partition = UserPartition(
            0,
            'first_partition',
            'First Partition',
            [
                Group(0, 'alpha'),
                Group(1, 'beta')
            ]
        )
        self.group1 = self.user_partition.groups[0]    # pylint: disable=no-member
        self.group2 = self.user_partition.groups[1]    # pylint: disable=no-member
        self.course = CourseFactory.create(user_partitions=[self.user_partition])
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.subsection = ItemFactory.create(parent=self.section, category='sequential', display_name='Test Subsection')
        self.vertical = ItemFactory.create(parent=self.subsection, category='vertical', display_name='Test Unit')
        self.video = ItemFactory.create(parent=self.vertical, category='video', display_name='Test Video 1')


class XBlockValidationTest(LmsXBlockMixinTestCase):
    """
    Unit tests for XBlock validation
    """
    def setUp(self):
        super(XBlockValidationTest, self).setUp()
        self.build_course()

    def verify_validation_message(self, message, expected_message, expected_message_type):
        """
        Verify that the validation message has the expected validation message and type.
        """
        self.assertEqual(message.text, expected_message)
        self.assertEqual(message.type, expected_message_type)

    def test_validate_full_group_access(self):
        """
        Test the validation messages produced for an xblock with full group access.
        """
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 0)

    def test_validate_restricted_group_access(self):
        """
        Test the validation messages produced for an xblock with a valid group access restriction
        """
        self.video.group_access[self.user_partition.id] = [self.group1.id, self.group2.id]  # pylint: disable=no-member
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 0)

    def test_validate_invalid_user_partition(self):
        """
        Test the validation messages produced for an xblock referring to a non-existent user partition.
        """
        self.video.group_access[999] = [self.group1.id]
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 1)
        self.verify_validation_message(
            validation.messages[0],
            u"This xblock refers to a deleted or invalid content group configuration.",
            ValidationMessage.ERROR,
        )

    def test_validate_invalid_group(self):
        """
        Test the validation messages produced for an xblock referring to a non-existent group.
        """
        self.video.group_access[self.user_partition.id] = [self.group1.id, 999]    # pylint: disable=no-member
        validation = self.video.validate()
        self.assertEqual(len(validation.messages), 1)
        self.verify_validation_message(
            validation.messages[0],
            u"This xblock refers to a deleted or invalid content group.",
            ValidationMessage.ERROR,
        )


class XBlockGroupAccessTest(LmsXBlockMixinTestCase):
    """
    Unit tests for XBlock group access.
    """
    def setUp(self):
        super(XBlockGroupAccessTest, self).setUp()
        self.build_course()

    def test_is_visible_to_group(self):
        """
        Test the behavior of is_visible_to_group.
        """
        # All groups are visible for an unrestricted xblock
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group1))
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group2))

        # Verify that all groups are visible if the set of group ids is empty
        self.video.group_access[self.user_partition.id] = []    # pylint: disable=no-member
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group1))
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group2))

        # Verify that only specified groups are visible
        self.video.group_access[self.user_partition.id] = [self.group1.id]    # pylint: disable=no-member
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group1))
        self.assertFalse(self.video.is_visible_to_group(self.user_partition, self.group2))

        # Verify that having an invalid user partition does not affect group visibility of other partitions
        self.video.group_access[999] = [self.group1.id]
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group1))
        self.assertFalse(self.video.is_visible_to_group(self.user_partition, self.group2))

        # Verify that group access is still correct even with invalid group ids
        self.video.group_access.clear()
        self.video.group_access[self.user_partition.id] = [self.group2.id, 999]    # pylint: disable=no-member
        self.assertFalse(self.video.is_visible_to_group(self.user_partition, self.group1))
        self.assertTrue(self.video.is_visible_to_group(self.user_partition, self.group2))


class OpenAssessmentBlockMixinTestCase(ModuleStoreTestCase):
    """
    Tests for OpenAssessmentBlock mixin.
    """

    def setUp(self):
        super(OpenAssessmentBlockMixinTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.section = ItemFactory.create(parent=self.course, category='chapter', display_name='Test Section')
        self.open_assessment = ItemFactory.create(
            parent=self.section,
            category="openassessment",
            display_name="untitled",
        )

    def test_has_score(self):
        """
        Test has_score is true for ora2 problems.
        """
        self.assertTrue(self.open_assessment.has_score)


@ddt.ddt
class XBlockGetParentTest(LmsXBlockMixinTestCase):
    """
    Test that XBlock.get_parent returns correct results with each modulestore
    backend.
    """
    def _pre_setup(self):
        # load the one xml course into the xml store
        update_module_store_settings(
            settings.MODULESTORE,
            mappings={'edX/toy/2012_Fall': ModuleStoreEnum.Type.xml},
            xml_store_options={
                'data_dir': settings.COMMON_TEST_DATA_ROOT  # where toy course lives
            },
        )
        super(XBlockGetParentTest, self)._pre_setup()

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split, ModuleStoreEnum.Type.xml)
    def test_parents(self, modulestore_type):
        with self.store.default_store(modulestore_type):

            # setting up our own local course tree here, since it needs to be
            # created with the correct modulestore type.

            if modulestore_type == 'xml':
                course_key = self.store.make_course_key('edX', 'toy', '2012_Fall')
            else:
                course_key = self.create_toy_course('edX', 'toy', '2012_Fall_copy')
            course = self.store.get_course(course_key)

            self.assertIsNone(course.get_parent())

            def recurse(parent):
                """
                Descend the course tree and ensure the result of get_parent()
                is the expected one.
                """
                visited = []
                for child in parent.get_children():
                    self.assertEqual(parent.location, child.get_parent().location)
                    visited.append(child)
                    visited += recurse(child)
                return visited

            visited = recurse(course)
            self.assertEqual(len(visited), 28)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_parents_draft_content(self, modulestore_type):
        # move the video to the new vertical
        with self.store.default_store(modulestore_type):
            self.build_course()
            new_vertical = ItemFactory.create(parent=self.subsection, category='vertical', display_name='New Test Unit')
            child_to_move_location = self.video.location.for_branch(None)
            new_parent_location = new_vertical.location.for_branch(None)
            old_parent_location = self.vertical.location.for_branch(None)

            with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
                self.assertIsNone(self.course.get_parent())

                with self.store.bulk_operations(self.course.id):
                    user_id = ModuleStoreEnum.UserID.test

                    old_parent = self.store.get_item(old_parent_location)
                    old_parent.children.remove(child_to_move_location)
                    self.store.update_item(old_parent, user_id)

                    new_parent = self.store.get_item(new_parent_location)
                    new_parent.children.append(child_to_move_location)
                    self.store.update_item(new_parent, user_id)

                    # re-fetch video from draft store
                    video = self.store.get_item(child_to_move_location)

                    self.assertEqual(
                        new_parent_location,
                        video.get_parent().location
                    )
            with self.store.branch_setting(ModuleStoreEnum.Branch.published_only):
                # re-fetch video from published store
                video = self.store.get_item(child_to_move_location)
                self.assertEqual(
                    old_parent_location,
                    video.get_parent().location.for_branch(None)
                )
