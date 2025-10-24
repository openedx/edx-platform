# pylint: disable=unused-import
"""
Tests for Discussion API serializers
"""

import itertools
from unittest import mock
from urllib.parse import urlparse

import ddt
import httpretty
from django.test.client import RequestFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.util.testing import UrlResetMixin
from lms.djangoapps.discussion.django_comment_client.tests.utils import ForumsEnableMixin
from lms.djangoapps.discussion.rest_api.serializers import CommentSerializer, ThreadSerializer, get_context
from lms.djangoapps.discussion.rest_api.tests.utils import (
    ForumMockUtilsMixin,
    make_minimal_cs_comment,
    make_minimal_cs_thread,
    parsed_body,
)
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.django_comment_common.comment_client.comment import Comment
from openedx.core.djangoapps.django_comment_common.comment_client.thread import Thread
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_STUDENT,
    Role,
)


@ddt.ddt
class CommentSerializerDeserializationTest(ForumsEnableMixin, ForumMockUtilsMixin, SharedModuleStoreTestCase):
    """Tests for ThreadSerializer deserialization."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    def setUp(self):
        super().setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.models.forum_api.get_course_id_by_comment"
        )
        self.mock_get_course_id_by_comment = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = mock.patch(
            "openedx.core.djangoapps.django_comment_common.comment_client.thread.forum_api.get_course_id_by_thread"
        )
        self.mock_get_course_id_by_thread = patcher.start()
        self.addCleanup(patcher.stop)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user
        self.minimal_data = {
            "thread_id": "test_thread",
            "raw_body": "Test body",
        }
        self.existing_comment = Comment(**make_minimal_cs_comment({
            "id": "existing_comment",
            "thread_id": "dummy",
            "body": "Original body",
            "user_id": str(self.user.id),
            "username": self.user.username,
            "course_id": str(self.course.id),
        }))

    def save_and_reserialize(self, data, instance=None):
        """
        Create a serializer with the given data, ensure that it is valid, save
        the result, and return the full comment data from the serializer.
        """
        context = get_context(
            self.course,
            self.request,
            make_minimal_cs_thread({"course_id": str(self.course.id)})
        )
        serializer = CommentSerializer(
            instance,
            data=data,
            partial=(instance is not None),
            context=context
        )
        assert serializer.is_valid()
        serializer.save()
        return serializer.data

    @ddt.data(None, "test_parent")
    def test_create_success(self, parent_id):
        data = self.minimal_data.copy()
        if parent_id:
            data["parent_id"] = parent_id
            self.register_get_comment_response({"thread_id": "test_thread", "id": parent_id})
        self.register_post_comment_response(
            {"id": "test_comment", "username": self.user.username},
            thread_id="test_thread",
            parent_id=parent_id
        )
        saved = self.save_and_reserialize(data)
        expected_url = (
            f"/api/v1/comments/{parent_id}" if parent_id else
            "/api/v1/threads/test_thread/comments"
        )
        self.check_mock_called("create_parent_comment")
        params = {
            'course_id': str(self.course.id),
            'body': 'Test body',
            'user_id': str(self.user.id),
            'anonymous': False,
            'anonymous_to_peers': False,
            'thread_id': 'test_thread',
        }
        if not data:
            self.check_mock_called_with(
                "create_parent_comment",
                0,
                **params,
            )
        assert saved['id'] == 'test_comment'
        assert saved['parent_id'] == parent_id

    def test_create_all_fields(self):
        data = self.minimal_data.copy()
        data["parent_id"] = "test_parent"
        data["endorsed"] = True
        self.register_get_comment_response({"thread_id": "test_thread", "id": "test_parent"})
        self.register_post_comment_response(
            {"id": "test_comment", "username": self.user.username},
            thread_id="test_thread",
            parent_id="test_parent"
        )
        self.save_and_reserialize(data)
        params = {
            'course_id': str(self.course.id),
            'body': 'Test body',
            'user_id': str(self.user.id),
            'endorsed': True,
            'anonymous': False,
            'anonymous_to_peers': False,
            'parent_comment_id': 'test_parent',
        }
        self.check_mock_called("create_parent_comment")
        self.check_mock_called_with(
            "create_child_comment",
            0,
            **params
        )

    def test_update_all(self):
        cs_response_data = self.existing_comment.attributes.copy()
        cs_response_data["endorsement"] = {
            "user_id": str(self.user.id),
            "time": "2015-06-05T00:00:00Z",
        }
        self.register_put_comment_response(cs_response_data)
        data = {"raw_body": "Edited body", "endorsed": True}
        self.register_get_thread_response(
            make_minimal_cs_thread({
                "id": "dummy",
                "course_id": str(self.course.id),
            })
        )
        saved = self.save_and_reserialize(data, instance=self.existing_comment)

        params = {
            'body': 'Edited body',
            'course_id': str(self.course.id),
            'user_id': str(self.user.id),
            'anonymous': False,
            'anonymous_to_peers': 'False',
            'endorsed': 'True',
            'endorsement_user_id': str(self.user.id),
            'editing_user_id': str(self.user.id),
        }
        self.check_mock_called("update_comment")
        for key in data:
            assert saved[key] == data[key]
        assert saved['endorsed_by'] == self.user.username
        assert saved['endorsed_at'] == '2015-06-05T00:00:00Z'

    @ddt.data("", " ")
    def test_update_empty_raw_body(self, value):
        serializer = CommentSerializer(
            self.existing_comment,
            data={"raw_body": value},
            partial=True,
            context=get_context(self.course, self.request)
        )
        assert not serializer.is_valid()
        assert serializer.errors == {'raw_body': ['This field may not be blank.']}

    def test_create_parent_id_nonexistent(self):
        self.register_get_comment_error_response("bad_parent", 404)
        data = self.minimal_data.copy()
        data["parent_id"] = "bad_parent"
        context = get_context(self.course, self.request, make_minimal_cs_thread())
        serializer = CommentSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'non_field_errors': ['parent_id does not identify a comment in the thread identified by thread_id.']
        }

    def test_create_parent_id_wrong_thread(self):
        self.register_get_comment_response({"thread_id": "different_thread", "id": "test_parent"})
        data = self.minimal_data.copy()
        data["parent_id"] = "test_parent"
        context = get_context(self.course, self.request, make_minimal_cs_thread())
        serializer = CommentSerializer(data=data, context=context)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'non_field_errors': ['parent_id does not identify a comment in the thread identified by thread_id.']
        }

    def test_create_anonymous(self):
        """
        Test that serializer correctly deserializes the anonymous field when
        creating a new comment.
        """
        self.register_post_comment_response({"username": self.user.username}, thread_id="test_thread")
        data = self.minimal_data.copy()
        data["anonymous"] = True
        self.save_and_reserialize(data)
        call_args = self.get_mock_func_calls("create_parent_comment")[0]
        args, kwargs = call_args
        assert kwargs['anonymous']

    def test_create_anonymous_to_peers(self):
        """
        Test that serializer correctly deserializes the anonymous_to_peers
        field when creating a new comment.
        """
        self.register_post_comment_response({"username": self.user.username}, thread_id="test_thread")
        data = self.minimal_data.copy()
        data["anonymous_to_peers"] = True
        self.save_and_reserialize(data)
        call_args = self.get_mock_func_calls("create_parent_comment")[-1]
        args, kwargs = call_args
        assert kwargs['anonymous_to_peers']

    @ddt.data(None, -1, 0, 2, 5)
    def test_create_parent_id_too_deep(self, max_depth):
        with mock.patch("lms.djangoapps.discussion.django_comment_client.utils.MAX_COMMENT_DEPTH", max_depth):
            data = self.minimal_data.copy()
            context = get_context(self.course, self.request, make_minimal_cs_thread())
            if max_depth is None or max_depth >= 0:
                if max_depth != 0:
                    self.register_get_comment_response({
                        "id": "not_too_deep",
                        "thread_id": "test_thread",
                        "depth": max_depth - 1 if max_depth else 100
                    })
                    data["parent_id"] = "not_too_deep"
                else:
                    data["parent_id"] = None
                serializer = CommentSerializer(data=data, context=context)
                assert serializer.is_valid(), serializer.errors
            if max_depth is not None:
                if max_depth >= 0:
                    self.register_get_comment_response({
                        "id": "too_deep",
                        "thread_id": "test_thread",
                        "depth": max_depth
                    })
                    data["parent_id"] = "too_deep"
                else:
                    data["parent_id"] = None
                serializer = CommentSerializer(data=data, context=context)
                assert not serializer.is_valid()
                assert serializer.errors == {'non_field_errors': ['Comment level is too deep.']}

    def test_create_endorsed(self):
        # TODO: The comments service doesn't populate the endorsement field on
        # comment creation, so this is sadly realistic
        self.register_post_comment_response({"username": self.user.username}, thread_id="test_thread")
        data = self.minimal_data.copy()
        data["endorsed"] = True
        saved = self.save_and_reserialize(data)

        params = {
            'course_id': str(self.course.id),
            'body': 'Test body',
            'user_id': str(self.user.id),
            'endorsed': True,
            'anonymous': False,
            'anonymous_to_peers': False,
            'thread_id': 'test_thread',
        }
        self.check_mock_called("create_parent_comment")
        self.check_mock_called_with(
            "create_parent_comment",
            -1,
            **params
        )
        assert saved['endorsed']
        assert saved['endorsed_by'] is None
        assert saved['endorsed_by_label'] is None
        assert saved['endorsed_at'] is None


@ddt.ddt
class ThreadSerializerDeserializationTest(
        ForumsEnableMixin,
        ForumMockUtilsMixin,
        UrlResetMixin,
        SharedModuleStoreTestCase
):
    """Tests for ThreadSerializer deserialization."""
    @classmethod
    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        """Stop patches after tests complete."""
        super().tearDownClass()
        super().disposeForumMocks()

    @mock.patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        httpretty.reset()
        httpretty.enable()
        self.addCleanup(httpretty.reset)
        self.addCleanup(httpretty.disable)
        patcher = mock.patch(
            'openedx.core.djangoapps.discussions.config.waffle.ENABLE_FORUM_V2.is_enabled',
            return_value=True
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.user = UserFactory.create()
        self.register_get_user_response(self.user)
        self.request = RequestFactory().get("/dummy")
        self.request.user = self.user
        self.minimal_data = {
            "course_id": str(self.course.id),
            "topic_id": "test_topic",
            "type": "discussion",
            "title": "Test Title",
            "raw_body": "Test body",
        }
        self.existing_thread = Thread(**make_minimal_cs_thread({
            "id": "existing_thread",
            "course_id": str(self.course.id),
            "commentable_id": "original_topic",
            "thread_type": "discussion",
            "title": "Original Title",
            "body": "Original body",
            "user_id": str(self.user.id),
            "username": self.user.username,
            "read": "False",
            "endorsed": "False"
        }))

    def save_and_reserialize(self, data, instance=None):
        """
        Create a serializer with the given data and (if updating) instance,
        ensure that it is valid, save the result, and return the full thread
        data from the serializer.
        """
        serializer = ThreadSerializer(
            instance,
            data=data,
            partial=(instance is not None),
            context=get_context(self.course, self.request)
        )
        assert serializer.is_valid()
        serializer.save()
        return serializer.data

    def test_create_minimal(self):
        self.register_post_thread_response({"id": "test_id", "username": self.user.username})
        saved = self.save_and_reserialize(self.minimal_data)
        params = {
            'course_id': str(self.course.id),
            'commentable_id': 'test_topic',
            'thread_type': 'discussion',
            'title': 'Test Title',
            'body': 'Test body',
            'user_id': str(self.user.id),
            'anonymous': False,
            'anonymous_to_peers': False,
        }
        self.check_mock_called("create_thread")
        self.check_mock_called_with(
            "create_thread",
            -1,
            **params
        )
        assert saved['id'] == 'test_id'

    def test_create_type(self):
        self.register_post_thread_response({"id": "test_id", "username": self.user.username})
        data = self.minimal_data.copy()
        data["type"] = "question"
        self.save_and_reserialize(data)

        data["type"] = "invalid_type"
        serializer = ThreadSerializer(data=data)
        assert not serializer.is_valid()

    def test_create_all_fields(self):
        self.register_post_thread_response({"id": "test_id", "username": self.user.username})
        data = self.minimal_data.copy()
        data["group_id"] = 42
        self.save_and_reserialize(data)
        params = {
            'course_id': str(self.course.id),
            'commentable_id': 'test_topic',
            'thread_type': 'discussion',
            'title': 'Test Title',
            'body': 'Test body',
            'user_id': str(self.user.id),
            'group_id': 42,
            'anonymous': False,
            'anonymous_to_peers': False,
        }
        self.check_mock_called("create_thread")
        self.check_mock_called_with(
            "create_thread",
            -1,
            **params
        )

    def test_create_anonymous(self):
        """
        Test that serializer correctly deserializes the anonymous field when
        creating a new thread.
        """
        self.register_post_thread_response({"id": "test_id", "username": self.user.username})
        data = self.minimal_data.copy()
        data["anonymous"] = True
        self.save_and_reserialize(data)
        call_args = self.get_mock_func_calls("create_thread")[0]
        args, kwargs = call_args
        assert kwargs['anonymous']

    def test_create_anonymous_to_peers(self):
        """
        Test that serializer correctly deserializes the anonymous_to_peers field
        when creating a new thread.
        """
        self.register_post_thread_response({"id": "test_id", "username": self.user.username})
        data = self.minimal_data.copy()
        data["anonymous_to_peers"] = True
        self.save_and_reserialize(data)
        call_args = self.get_mock_func_calls("create_thread")[0]
        args, kwargs = call_args
        assert kwargs['anonymous_to_peers']
