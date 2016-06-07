# -*- coding: utf-8 -*-
"""Test for Discussion Xmodule functional logic."""
import ddt
from django.core.urlresolvers import reverse
from mock import Mock
from . import BaseTestXmodule
from course_api.blocks.tests.helpers import deserialize_usage_key
from course_blocks.tests.helpers import EnableTransformerRegistryMixin
from courseware.module_render import get_module_for_descriptor_internal
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.discussion_module import DiscussionModule
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory, ItemFactory


@ddt.ddt
class DiscussionModuleTest(BaseTestXmodule, EnableTransformerRegistryMixin, SharedModuleStoreTestCase):
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

    def test_discussion_student_view_data(self):
        """
        Tests that course block api returns student_view_data for discussion module
        """
        course_key = ToyCourseFactory.create().id
        course_usage_key = self.store.make_course_usage_key(course_key)
        user = UserFactory.create()
        self.client.login(username=user.username, password='test')
        CourseEnrollmentFactory.create(user=user, course_id=course_key)
        discussion_id = "test_discussion_module_id"
        ItemFactory.create(
            parent_location=course_usage_key,
            category='discussion',
            discussion_id=discussion_id,
            discussion_category='Category discussion',
            discussion_target='Target Discussion',
        )

        url = reverse('blocks_in_block_tree', kwargs={'usage_key_string': unicode(course_usage_key)})
        query_params = {
            'depth': 'all',
            'username': user.username,
            'block_types_filter': 'discussion',
            'student_view_data': 'discussion'
        }
        response = self.client.get(url, query_params)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data['root'], unicode(course_usage_key))  # pylint: disable=no-member
        for block_key_string, block_data in response.data['blocks'].iteritems():  # pylint: disable=no-member
            block_key = deserialize_usage_key(block_key_string, course_key)
            self.assertEquals(block_data['id'], block_key_string)
            self.assertEquals(block_data['type'], block_key.block_type)
            self.assertEquals(block_data['display_name'], self.store.get_item(block_key).display_name or '')
            self.assertEqual(block_data['student_view_data'], {"topic_id": discussion_id})
