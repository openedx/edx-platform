"""
Tests for the discussion xblock.

Most of the tests are in common/xblock/xblock_discussion, here are only
tests for functionalities that require django API, and lms specific
functionalities.
"""

import uuid

import ddt
import json
import mock

from django.core.urlresolvers import reverse
from course_api.blocks.tests.helpers import deserialize_usage_key
from courseware.module_render import get_module_for_descriptor_internal
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xblock.field_data import DictFieldData
from xblock.fragment import Fragment
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.factories import ToyCourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from lms.djangoapps.courseware.tests import XModuleRenderingTestBase

from xblock_discussion import DiscussionXBlock, loader


@ddt.ddt
class TestDiscussionXBlock(XModuleRenderingTestBase):
    """
    Base class for tests
    """

    PATCH_DJANGO_USER = True

    def setUp(self):
        """
        Set up the xblock runtime, test course, discussion, and user.
        """
        super(TestDiscussionXBlock, self).setUp()
        self.patchers = []
        self.course_id = "test_course"
        self.runtime = self.new_module_runtime()
        self.runtime.modulestore = mock.Mock()

        self.discussion_id = str(uuid.uuid4())
        self.data = DictFieldData({
            'discussion_id': self.discussion_id
        })
        scope_ids = mock.Mock()
        scope_ids.usage_id.course_key = self.course_id
        self.block = DiscussionXBlock(
            self.runtime,
            field_data=self.data,
            scope_ids=scope_ids
        )
        self.block.xmodule_runtime = mock.Mock()

        if self.PATCH_DJANGO_USER:
            self.django_user_canary = object()
            self.django_user_mock = self.add_patcher(
                mock.patch.object(DiscussionXBlock, "django_user", new_callable=mock.PropertyMock)
            )
            self.django_user_mock.return_value = self.django_user_canary

    def add_patcher(self, patcher):
        """
        Registers a patcher object, and returns mock. This patcher will be disabled after the test.
        """
        self.patchers.append(patcher)
        return patcher.start()

    def tearDown(self):
        """
        Tears down any patchers added during tests.
        """
        super(TestDiscussionXBlock, self).tearDown()
        for patcher in self.patchers:
            patcher.stop()


class TestGetDjangoUser(TestDiscussionXBlock):
    """
    Tests for the django_user property.
    """

    PATCH_DJANGO_USER = False

    def setUp(self):
        """
        Mock the user service and runtime.
        """
        super(TestGetDjangoUser, self).setUp()
        self.django_user = object()
        self.user_service = mock.Mock()
        self.add_patcher(
            mock.patch.object(self.runtime, "service", return_value=self.user_service)
        )
        self.user_service._django_user = self.django_user  # pylint: disable=protected-access

    def test_django_user(self):
        """
        Tests that django_user users returns _django_user attribute
        of the user service.
        """
        actual_user = self.block.django_user
        self.runtime.service.assert_called_once_with(
            self.block, 'user')
        self.assertEqual(actual_user, self.django_user)

    def test_django_user_handles_missing_service(self):
        """
        Tests that get_django gracefully handles missing user service.
        """
        self.runtime.service.return_value = None
        self.assertEqual(self.block.django_user, None)


@ddt.ddt
class TestViews(TestDiscussionXBlock):
    """
    Tests for student_view and author_view.
    """

    def setUp(self):
        """
        Mock the methods needed for these tests.
        """
        super(TestViews, self).setUp()
        self.template_canary = u'canary'
        self.render_template = mock.Mock()
        self.render_template.return_value = self.template_canary
        self.block.runtime.render_template = self.render_template
        self.has_permission_mock = mock.Mock()
        self.has_permission_mock.return_value = False
        self.block.has_permission = self.has_permission_mock

    def get_template_context(self):
        """
        Returns context passed to rendering of the django template
        (rendered by runtime).
        """
        self.assertEqual(self.render_template.call_count, 1)
        return self.render_template.call_args_list[0][0][1]

    def get_rendered_template(self):
        """
        Returns the name of the template rendered by runtime.
        """
        self.assertEqual(self.render_template.call_count, 1)
        return self.render_template.call_args_list[0][0][0]

    def test_studio_view(self):
        """
        Test for the studio view.
        """
        fragment = self.block.author_view()
        self.assertIsInstance(fragment, Fragment)
        self.assertEqual(fragment.content, self.template_canary)
        self.render_template.assert_called_once_with(
            'discussion/_discussion_inline_studio.html',
            {'discussion_id': self.discussion_id}
        )

    @ddt.data(
        (False, False, False),
        (True, False, False),
        (False, True, False),
        (False, False, True),
    )
    def test_student_perms_are_correct(self, permissions):
        """
        Test that context will get proper permissions.
        """
        permission_dict = {
            'create_thread': permissions[0],
            'create_comment': permissions[1],
            'create_sub_comment': permissions[2]
        }

        expected_permissions = {
            'can_create_thread': permission_dict['create_thread'],
            'can_create_comment': permission_dict['create_comment'],
            'can_create_subcomment': permission_dict['create_sub_comment'],
        }

        self.block.has_permission = lambda perm: permission_dict[perm]
        with mock.patch.object(loader, 'render_template', mock.Mock):
            self.block.student_view()

        context = self.get_template_context()

        for permission_name, expected_value in expected_permissions.items():
            self.assertEqual(expected_value, context[permission_name])

    def test_js_init(self):
        """
        Test proper js init function is called.
        """
        with mock.patch.object(loader, 'render_template', mock.Mock):
            fragment = self.block.student_view()
        self.assertEqual(fragment.js_init_fn, 'DiscussionInlineBlock')


@ddt.ddt
class TestTemplates(TestDiscussionXBlock):
    """
    Tests rendering of templates.
    """

    def test_has_permission(self):
        """
        Test for has_permission method.
        """
        permission_canary = object()
        with mock.patch('django_comment_client.permissions.has_permission', return_value=permission_canary) as has_perm:
            actual_permission = self.block.has_permission("test_permission")
        self.assertEqual(actual_permission, permission_canary)
        has_perm.assert_called_once_with(self.django_user_canary, 'test_permission', 'test_course')

    def test_studio_view(self):
        """Test for studio view."""
        fragment = self.block.author_view({})
        self.assertIn('data-discussion-id="{}"'.format(self.discussion_id), fragment.content)

    @ddt.data(
        (True, False, False),
        (False, True, False),
        (False, False, True),
    )
    def test_student_perms_are_correct(self, permissions):
        """
        Test for lms view.
        """
        permission_dict = {
            'create_thread': permissions[0],
            'create_comment': permissions[1],
            'create_sub_comment': permissions[2]
        }

        self.block.has_permission = lambda perm: permission_dict[perm]
        fragment = self.block.student_view()

        self.assertIn('data-discussion-id="{}"'.format(self.discussion_id), fragment.content)
        self.assertIn('data-user-create-comment="{}"'.format(json.dumps(permissions[1])), fragment.content)
        self.assertIn('data-user-create-subcomment="{}"'.format(json.dumps(permissions[2])), fragment.content)
        if permissions[0]:
            self.assertIn("Add a Post", fragment.content)
        else:
            self.assertNotIn("Add a Post", fragment.content)


@ddt.ddt
class TestXBlockInCourse(SharedModuleStoreTestCase):
    """
    Test the discussion xblock as rendered in the course and course API.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up a user, course, and discussion XBlock for use by tests.
        """
        super(TestXBlockInCourse, cls).setUpClass()
        cls.user = UserFactory.create()
        cls.course = ToyCourseFactory.create()
        cls.course_key = cls.course.id
        cls.course_usage_key = cls.store.make_course_usage_key(cls.course_key)
        cls.discussion_id = "test_discussion_xblock_id"
        cls.discussion = ItemFactory.create(
            parent_location=cls.course_usage_key,
            category='discussion',
            discussion_id=cls.discussion_id,
            discussion_category='Category discussion',
            discussion_target='Target Discussion',
        )
        CourseEnrollmentFactory.create(user=cls.user, course_id=cls.course_key)

    def get_root(self, block):
        """
        Return root of the block.
        """
        while block.parent:
            block = block.get_parent()
        return block

    def test_html_with_user(self):
        """
        Test rendered DiscussionXBlock permissions.
        """
        discussion_xblock = get_module_for_descriptor_internal(
            user=self.user,
            descriptor=self.discussion,
            student_data=mock.Mock(name='student_data'),
            course_id=self.course.id,
            track_function=mock.Mock(name='track_function'),
            xqueue_callback_url_prefix=mock.Mock(name='xqueue_callback_url_prefix'),
            request_token='request_token',
        )

        fragment = discussion_xblock.render('student_view')
        html = fragment.content
        self.assertIn('data-user-create-comment="false"', html)
        self.assertIn('data-user-create-subcomment="false"', html)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_discussion_render_successfully_with_orphan_parent(self, default_store):
        """
        Test that discussion xblock render successfully
        if discussion xblock is child of an orphan.
        """
        with self.store.default_store(default_store):
            orphan_sequential = self.store.create_item(self.user.id, self.course.id, 'sequential')

            vertical = self.store.create_child(
                self.user.id,
                orphan_sequential.location,
                'vertical',
                block_id=self.course.location.block_id
            )

            discussion = self.store.create_child(
                self.user.id,
                vertical.location,
                'discussion',
                block_id=self.course.location.block_id
            )

            discussion = self.store.get_item(discussion.location)

            root = self.get_root(discussion)
            # Assert that orphan sequential is root of the discussion xblock.
            self.assertEqual(orphan_sequential.location.block_type, root.location.block_type)
            self.assertEqual(orphan_sequential.location.block_id, root.location.block_id)

            # Get xblock bound to a user and a descriptor.
            discussion_xblock = get_module_for_descriptor_internal(
                user=self.user,
                descriptor=discussion,
                student_data=mock.Mock(name='student_data'),
                course_id=self.course.id,
                track_function=mock.Mock(name='track_function'),
                xqueue_callback_url_prefix=mock.Mock(name='xqueue_callback_url_prefix'),
                request_token='request_token',
            )

            fragment = discussion_xblock.render('student_view')
            html = fragment.content

            self.assertIsInstance(discussion_xblock, DiscussionXBlock)
            self.assertIn('data-user-create-comment="false"', html)
            self.assertIn('data-user-create-subcomment="false"', html)

    def test_discussion_student_view_data(self):
        """
        Tests that course block api returns student_view_data for discussion xblock
        """
        self.client.login(username=self.user.username, password='test')
        url = reverse('blocks_in_block_tree', kwargs={'usage_key_string': unicode(self.course_usage_key)})
        query_params = {
            'depth': 'all',
            'username': self.user.username,
            'block_types_filter': 'discussion',
            'student_view_data': 'discussion'
        }
        response = self.client.get(url, query_params)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.data['root'], unicode(self.course_usage_key))  # pylint: disable=no-member
        for block_key_string, block_data in response.data['blocks'].iteritems():  # pylint: disable=no-member
            block_key = deserialize_usage_key(block_key_string, self.course_key)
            self.assertEquals(block_data['id'], block_key_string)
            self.assertEquals(block_data['type'], block_key.block_type)
            self.assertEquals(block_data['display_name'], self.store.get_item(block_key).display_name or '')
            self.assertEqual(block_data['student_view_data'], {"topic_id": self.discussion_id})


class TestXBlockQueryLoad(SharedModuleStoreTestCase):
    """
    Test the number of queries executed when rendering the XBlock.
    """

    def test_permissions_query_load(self):
        """
        Tests that the permissions queries are cached when rendering numerous discussion XBlocks.
        """
        user = UserFactory.create()
        course = ToyCourseFactory.create()
        course_key = course.id
        course_usage_key = self.store.make_course_usage_key(course_key)
        discussions = []

        for counter in range(5):
            discussion_id = 'test_discussion_{}'.format(counter)
            discussions.append(ItemFactory.create(
                parent_location=course_usage_key,
                category='discussion',
                discussion_id=discussion_id,
                discussion_category='Category discussion',
                discussion_target='Target Discussion',
            ))

        # 3 queries are required to do first discussion xblock render:
        # * django_comment_client_role
        # * django_comment_client_permission
        # * lms_xblock_xblockasidesconfig
        num_queries = 3
        for discussion in discussions:
            discussion_xblock = get_module_for_descriptor_internal(
                user=user,
                descriptor=discussion,
                student_data=mock.Mock(name='student_data'),
                course_id=course.id,
                track_function=mock.Mock(name='track_function'),
                xqueue_callback_url_prefix=mock.Mock(name='xqueue_callback_url_prefix'),
                request_token='request_token',
            )
            with self.assertNumQueries(num_queries):
                fragment = discussion_xblock.render('student_view')

            # Permissions are cached, so no queries required for subsequent renders
            num_queries = 0

            html = fragment.content
            self.assertIn('data-user-create-comment="false"', html)
            self.assertIn('data-user-create-subcomment="false"', html)
