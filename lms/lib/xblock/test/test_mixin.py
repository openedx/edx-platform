"""
Tests of the LMS XBlock Mixin
"""

from xblock.validation import ValidationMessage
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.partitions.partitions import Group, UserPartition


class LmsXBlockMixinTestCase(ModuleStoreTestCase):
    """
    Base class for XBlock mixin tests cases. A simple course with a single user partition is created
    in setUp for all subclasses to use.
    """

    def setUp(self):
        super(LmsXBlockMixinTestCase, self).setUp()
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
        self.video = ItemFactory.create(parent=self.subsection, category='video', display_name='Test Video')


class XBlockValidationTest(LmsXBlockMixinTestCase):
    """
    Unit tests for XBlock validation
    """

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
