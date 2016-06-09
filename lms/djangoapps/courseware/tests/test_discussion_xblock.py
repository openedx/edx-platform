"""
Tests for the new discussion xblock.

Most of the tests are in common/xblock/xblock_discussion, here are only
tests for functionalities that require django API, and lms specific
functionalities.
"""

import uuid

import ddt
import json
import mock

from xblock.field_data import DictFieldData
from xblock.fragment import Fragment, FragmentResource

from lms.djangoapps.courseware.tests import XModuleRenderingTestBase

from xblock_discussion import DiscussionXBlock, loader


@ddt.ddt
class TestDiscussionXblock(XModuleRenderingTestBase):
    """
    Base class for tests
    """

    PATCH_DJANGO_USER = True

    def setUp(self):
        """Set up function."""
        super(TestDiscussionXblock, self).setUp()
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
        """Registers a patcher object, and returns mock. This patcher will be disabled after the test"""
        self.patchers.append(patcher)
        return patcher.start()

    def tearDown(self):
        """Tears down after test."""
        super(TestDiscussionXblock, self).tearDown()
        for patcher in self.patchers:
            patcher.stop()


class TestGetDjangoUser(TestDiscussionXblock):
    """
    Tests for the django_user property.
    """

    PATCH_DJANGO_USER = False

    def setUp(self):
        """Set up function."""
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


class TestStudentView(TestDiscussionXblock):
    """
    Tests for the student_view function.
    """

    def setUp(self):
        """Set up function."""
        super(TestStudentView, self).setUp()
        self.block.student_view_lms = mock.Mock()
        self.block.student_view_studio = mock.Mock()

    def test_defaults_to_student_view_if_no_xmodule_runtime(self):
        """
        Tests that we show LMS version of the module when xmodule_runtime
        is not available.
        """
        del self.block.xmodule_runtime
        self.block.student_view()
        self.assertTrue(self.block.student_view_lms.called)
        self.assertFalse(self.block.student_view_studio.called)

    def test_returns_student_view_when_in_lms(self):
        """
        Tests that we show LMS version of the module when user
        is in LMS.
        """
        self.block.xmodule_runtime.is_author_mode = False
        self.block.student_view()
        self.assertFalse(self.block.student_view_studio.called)
        self.assertTrue(self.block.student_view_lms.called)

    def test_returns_studio_view_when_in_studio(self):
        """
        Tests that we show CMS version of the module when in CMS.
        """
        self.block.xmodule_runtime.is_author_mode = True
        self.block.student_view()
        self.assertTrue(self.block.student_view_studio.called)
        self.assertFalse(self.block.student_view_lms.called)


@ddt.ddt
class TestViews(TestDiscussionXblock):
    """
    Tests for student_view_lms and student_view_studio.
    """

    def setUp(self):
        """Set up function."""
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
        self.block.xmodule_runtime.is_author_mode = True
        fragment = self.block.student_view()
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
            'create_subcomment': permissions[2]
        }

        expected_permissions = {
            'can_create_thread': permission_dict['create_thread'],
            'can_create_comment': json.dumps(permission_dict['create_comment']),
            'can_create_subcomment': json.dumps(permission_dict['create_subcomment']),
        }

        self.block.has_permission = lambda perm: permission_dict[perm]
        self.block.xmodule_runtime.is_author_mode = False
        with mock.patch.object(loader, 'render_template', mock.Mock):
            self.block.student_view()

        context = self.get_template_context()

        for permission_name, expected_value in expected_permissions.items():
            self.assertEqual(expected_value, context[permission_name])

    def test_js_init(self):
        """
        Test proper js init function is called.
        """
        self.block.xmodule_runtime.is_author_mode = False
        with mock.patch.object(loader, 'render_template', mock.Mock):
            fragment = self.block.student_view()
        self.assertEqual(fragment.js_init_fn, 'DiscussionInlineBlock')

    def test_js_contents(self):
        """
        Test javascript is properly added as a resource.
        """
        self.block.xmodule_runtime.is_author_mode = False
        test_javascript = "some_javascript"
        with mock.patch.object(loader, 'render_template', return_value=test_javascript):
            fragment = self.block.student_view()
        self.assertEqual(len(fragment.resources), 1)
        expected_resource = FragmentResource(
            kind='text',
            data=test_javascript,
            mimetype='application/javascript',
            placement='foot'
        )
        self.assertEqual(expected_resource, fragment.resources[0])


@ddt.ddt
class TestTemplates(TestDiscussionXblock):
    """
    Tests rendering of templates.
    """

    def test_has_permission(self):
        """Test for has_permission method."""
        permission_canary = object()
        with mock.patch('django_comment_client.permissions.has_permission', return_value=permission_canary) as has_perm:
            actual_permission = self.block.has_permission("test_permission")
        self.assertEqual(actual_permission, permission_canary)
        has_perm.assert_called_once_with(self.django_user_canary, 'test_permission', 'test_course')

    def test_studio_view(self):
        """Test for studio view."""
        self.block.xmodule_runtime.is_author_mode = True
        fragment = self.block.student_view({})
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
            'create_subcomment': permissions[2]
        }

        self.block.has_permission = lambda perm: permission_dict[perm]
        self.block.xmodule_runtime.is_author_mode = False
        fragment = self.block.student_view()

        self.assertIn('data-discussion-id="{}"'.format(self.discussion_id), fragment.content)
        self.assertIn('data-user-create-comment="{}"'.format(json.dumps(permissions[1])), fragment.content)
        self.assertIn('data-user-create-subcomment="{}"'.format(json.dumps(permissions[2])), fragment.content)
        if permissions[0]:
            self.assertIn("Add a Post", fragment.content)
        else:
            self.assertNotIn("Add a Post", fragment.content)
