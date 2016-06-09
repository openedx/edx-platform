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
from lms.djangoapps.courseware.tests import XModuleRenderingTestBase

from xblock.field_data import DictFieldData

from xblock_discussion import DiscussionXBlock

@ddt.ddt
class TestDiscussionXblock(XModuleRenderingTestBase):
    """
    Base class for tests
    """

    def setUp(self):
        """Set up function."""
        super(TestDiscussionXblock, self).setUp()
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
        self.django_user_canary = object()
        self.django_user_patcher = mock.patch.object(DiscussionXBlock, "django_user", new_callable=mock.PropertyMock)
        self.django_user_mock = self.django_user_patcher.start()
        self.django_user_mock.return_value = self.django_user_canary

    def tearDown(self):
        """Cleans up after test"""
        self.django_user_patcher.stop()

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

