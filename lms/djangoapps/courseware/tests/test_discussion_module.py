# -*- coding: utf-8 -*-
"""Test for Discussion Xmodule functional logic."""
import ddt
from mock import Mock
from . import BaseTestXmodule
from courseware.module_render import get_module_for_descriptor_internal
from xmodule.discussion_module import DiscussionModule
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from student.tests.factories import UserFactory


@ddt.ddt
class DiscussionModuleTest(BaseTestXmodule):
    """Logic tests for Discussion Xmodule."""
    CATEGORY = "discussion"

    def test_html_with_user(self):
        discussion = get_module_for_descriptor_internal(
            user=self.users[0],
            descriptor=self.item_descriptor,
            student_data=Mock(name='student_data'),
            course_id=self.course.id,
            track_function=Mock(name='track_function'),
            xqueue_callback_url_prefix=Mock(name='xqueue_callback_url_prefix'),
            request_token='request_token',
        )

        fragment = discussion.render('student_view')
        html = fragment.content
        self.assertIn('data-user-create-comment="false"', html)
        self.assertIn('data-user-create-subcomment="false"', html)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_discussion_render_successfully_with_orphan_parent(self, default_store):
        """
        Test that discussion module render successfully
        if discussion module is child of an orphan.
        """
        user = UserFactory.create()
        store = modulestore()
        with store.default_store(default_store):
            course = store.create_course('testX', 'orphan', '123X', user.id)
            orphan_sequential = store.create_item(self.user.id, course.id, 'sequential')

            vertical = store.create_child(
                user.id,
                orphan_sequential.location,
                'vertical',
                block_id=course.location.block_id
            )

            discussion = store.create_child(
                user.id,
                vertical.location,
                'discussion',
                block_id=course.location.block_id
            )

            discussion = store.get_item(discussion.location)

            root = self.get_root(discussion)
            # Assert that orphan sequential is root of the discussion module.
            self.assertEqual(orphan_sequential.location.block_type, root.location.block_type)
            self.assertEqual(orphan_sequential.location.block_id, root.location.block_id)

            # Get module system bound to a user and a descriptor.
            discussion_module = get_module_for_descriptor_internal(
                user=user,
                descriptor=discussion,
                student_data=Mock(name='student_data'),
                course_id=course.id,
                track_function=Mock(name='track_function'),
                xqueue_callback_url_prefix=Mock(name='xqueue_callback_url_prefix'),
                request_token='request_token',
            )

            fragment = discussion_module.render('student_view')
            html = fragment.content

            self.assertIsInstance(discussion_module._xmodule, DiscussionModule)     # pylint: disable=protected-access
            self.assertIn('data-user-create-comment="false"', html)
            self.assertIn('data-user-create-subcomment="false"', html)

    def get_root(self, block):
        """
        Return root of the block.
        """
        while block.parent:
            block = block.get_parent()

        return block
