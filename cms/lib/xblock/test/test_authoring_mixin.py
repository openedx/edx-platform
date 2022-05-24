"""
Tests for the Studio authoring XBlock mixin.
"""


from xblock.core import XBlock
from xmodule.modulestore.tests.django_utils import TEST_DATA_MONGO_AMNESTY_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import MINIMUM_STATIC_PARTITION_ID, Group, UserPartition

from common.lib.xmodule.xmodule.tests.test_export import PureXBlock


class AuthoringMixinTestCase(ModuleStoreTestCase):
    """
    Tests the studio authoring XBlock mixin.
    """
    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE
    GROUP_NO_LONGER_EXISTS = "This group no longer exists"
    NO_RESTRICTIONS_MSG = "Access to this component is not restricted"
    NO_CONTENT_GROUP_MSG = "You can restrict access to this component to learners in specific content groups"
    CONTENT_GROUPS_TITLE = "Content Groups"
    STAFF_LOCKED = 'The unit that contains this component is hidden from learners'

    @XBlock.register_temp_plugin(PureXBlock, 'pure')
    def setUp(self):
        """
        Create a simple course with a video component.
        """
        super().setUp()
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
        pure = ItemFactory.create(
            category='pure',
            parent_location=vertical.location,
            display_name='Test Pure'
        )
        self.vertical_location = vertical.location
        self.video_location = video.location
        self.pure_location = pure.location
        self.pet_groups = [Group(1, 'Cat Lovers'), Group(2, 'Dog Lovers')]

    def create_content_groups(self, content_groups):
        """
        Create a cohorted user partition with the specified content groups.
        """
        # pylint: disable=attribute-defined-outside-init
        self.content_partition = UserPartition(
            MINIMUM_STATIC_PARTITION_ID,
            self.CONTENT_GROUPS_TITLE,
            'Contains Groups for Cohorted Courseware',
            content_groups,
            scheme_id='cohort'
        )
        self.course.user_partitions = [self.content_partition]
        self.store.update_item(self.course, self.user.id)

    def set_staff_only(self, item_location):
        """Make an item visible to staff only."""
        item = self.store.get_item(item_location)
        item.visible_to_staff_only = True
        self.store.update_item(item, self.user.id)

    def set_group_access(self, item_location, group_ids, partition_id=None):
        """
        Set group_access for the specified item to the specified group
        ids within the content partition.
        """
        item = self.store.get_item(item_location)
        item.group_access[self.content_partition.id if partition_id is None else partition_id] = group_ids
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

    def verify_visibility_view_does_not_contain(self, item_location, substrings):
        """
        Verify that an item's visibility view returns an html string
        that does NOT contain the provided substrings.
        """
        item = self.store.get_item(item_location)
        html = item.visibility_view().body_html()
        for string in substrings:
            self.assertNotIn(string, html)

    def test_html_no_partition(self):
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_GROUP_MSG])

    def test_html_empty_partition(self):
        self.create_content_groups([])
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_GROUP_MSG])

    def test_html_populated_partition(self):
        self.create_content_groups(self.pet_groups)
        self.verify_visibility_view_contains(
            self.video_location,
            [self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers']
        )

        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.NO_CONTENT_GROUP_MSG]
        )

    def test_html_no_partition_staff_locked(self):
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_GROUP_MSG])
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.STAFF_LOCKED, self.CONTENT_GROUPS_TITLE]
        )

    def test_html_empty_partition_staff_locked(self):
        self.create_content_groups([])
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(self.video_location, [self.NO_CONTENT_GROUP_MSG])
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.STAFF_LOCKED, self.CONTENT_GROUPS_TITLE]
        )

    def test_html_populated_partition_staff_locked(self):
        self.create_content_groups(self.pet_groups)
        self.set_staff_only(self.vertical_location)
        self.verify_visibility_view_contains(
            self.video_location,
            [self.STAFF_LOCKED, self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers']
        )

    def test_html_false_content_group(self):
        self.create_content_groups(self.pet_groups)
        self.set_group_access(self.video_location, ['false_group_id'])
        self.verify_visibility_view_contains(
            self.video_location,
            [self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers', self.GROUP_NO_LONGER_EXISTS]
        )
        self.verify_visibility_view_does_not_contain(
            self.video_location,
            [self.STAFF_LOCKED]
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
                self.STAFF_LOCKED,
                self.GROUP_NO_LONGER_EXISTS
            ]
        )

    def test_content_groups_message(self):
        """
        Test "no groups" messages.
        """
        self.verify_visibility_view_contains(
            self.video_location,
            [self.NO_RESTRICTIONS_MSG, self.NO_CONTENT_GROUP_MSG]
        )

    def test_pure_xblock_visibility(self):
        self.create_content_groups(self.pet_groups)
        self.verify_visibility_view_contains(
            self.pure_location,
            [self.CONTENT_GROUPS_TITLE, 'Cat Lovers', 'Dog Lovers']
        )

        self.verify_visibility_view_does_not_contain(
            self.pure_location,
            [self.NO_CONTENT_GROUP_MSG]
        )
