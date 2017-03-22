"""
Tests for the Studio authoring XBlock mixin.
"""

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition


class AuthoringMixinTestCase(ModuleStoreTestCase):
    """
    Tests the studio authoring XBlock mixin.
    """
    def setUp(self):
        """
        Create a simple course with a video component.
        """
        super(AuthoringMixinTestCase, self).setUp()
        self.course = CourseFactory.create()
        chapter = ItemFactory.create(
            category='chapter',
            parent_location=self.course.location,
            display_name='Test Chapter'
        )
        sequential = ItemFactory.create(
            category='sequential',
            parent_location=chapter.location,
            display_name='Test Sequential'
        )
        vertical = ItemFactory.create(
            category='vertical',
            parent_location=sequential.location,
            display_name='Test Vertical'
        )
        video = ItemFactory.create(
            category='video',
            parent_location=vertical.location,
            display_name='Test Vertical'
        )
        self.vertical_location = vertical.location
        self.video_location = video.location
        self.pet_groups = [Group(1, 'Cat Lovers'), Group(2, 'Dog Lovers')]

    def create_content_groups(self, content_groups):
        """
        Create a cohorted user partition with the specified content groups.
        """
        # pylint: disable=attribute-defined-outside-init
        self.content_partition = UserPartition(
            1,
            'Content Groups',
            'Contains Groups for Cohorted Courseware',
            content_groups,
            scheme_id='cohort'
        )
        self.course.user_partitions = [self.content_partition]
        self.store.update_item(self.course, self.user.id)

    def create_verification_user_partitions(self, checkpoint_names):
        """
        Create user partitions for verification checkpoints.
        """
        scheme = UserPartition.get_scheme("verification")
        self.course.user_partitions = [
            UserPartition(
                id=0,
                name=checkpoint_name,
                description="Verification checkpoint",
                scheme=scheme,
                groups=[
                    Group(scheme.ALLOW, "Completed verification at {}".format(checkpoint_name)),
                    Group(scheme.DENY, "Did not complete verification at {}".format(checkpoint_name)),
                ],
            )
            for checkpoint_name in checkpoint_names
        ]
        self.store.update_item(self.course, self.user.id)

    def set_staff_only(self, item_location):
        """Make an item visible to staff only."""
        item = self.store.get_item(item_location)
        item.visible_to_staff_only = True
        self.store.update_item(item, self.user.id)

    def set_group_access(self, item_location, group_ids):
        """
        Set group_access for the specified item to the specified group
        ids within the content partition.
        """
        item = self.store.get_item(item_location)
        item.group_access[self.content_partition.id] = group_ids
        self.store.update_item(item, self.user.id)

    def verify_visibility_view_contains(self, item_location, substrings):
        """
        Verify that an item's visibility view returns an html string
        containing all the expected substrings.
        """
        item = self.store.get_item(item_location)
        html = item.visibility_view().body_html()
        for string in substrings:
            self.assertIn(string, html)

    # def test_html_no_partition(self):
        # TODO: update with UX changes
        # self.verify_visibility_view_contains(self.video_location, 'No content groups exist')

    def test_html_empty_partition(self):
        self.create_content_groups([])
        # TODO: update with UX changes
        # self.verify_visibility_view_contains(self.video_location, 'No content groups exist')

    def test_html_populated_partition(self):
        self.create_content_groups(self.pet_groups)
        self.verify_visibility_view_contains(self.video_location, ['Cat Lovers', 'Dog Lovers'])

    def test_html_no_partition_staff_locked(self):
        self.set_staff_only(self.vertical_location)
        # TODO: update with UX changes
        # self.verify_visibility_view_contains(self.video_location, ['No content groups exist'])

    def test_html_empty_partition_staff_locked(self):
        self.create_content_groups([])
        self.set_staff_only(self.vertical_location)
        # TODO: update with UX changes
        # self.verify_visibility_view_contains(self.video_location, 'No content groups exist')

    def test_html_populated_partition_staff_locked(self):
        self.create_content_groups(self.pet_groups)
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(
            self.video_location,
            ['The Unit this component is contained in is hidden from students.', 'Cat Lovers', 'Dog Lovers']
        )

    def test_html_false_content_group(self):
        self.create_content_groups(self.pet_groups)
        self.set_group_access(self.video_location, ['false_group_id'])
        self.verify_visibility_view_contains(
            self.video_location, ['Cat Lovers', 'Dog Lovers', 'Content group no longer exists.']
        )

    def test_html_false_content_group_staff_locked(self):
        self.create_content_groups(self.pet_groups)
        self.set_staff_only(self.vertical_location)
        self.set_group_access(self.video_location, ['false_group_id'])
        self.verify_visibility_view_contains(
            self.video_location,
            [
                'Cat Lovers',
                'Dog Lovers',
                'The Unit this component is contained in is hidden from students.',
                'Content group no longer exists.'
            ]
        )

    def test_html_verification_checkpoints(self):
        self.create_verification_user_partitions(["Midterm A", "Midterm B"])
        self.verify_visibility_view_contains(
            self.video_location,
            [
                "Verification Checkpoint",
                "Midterm A",
                "Midterm B",
            ]
        )
