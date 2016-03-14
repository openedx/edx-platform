"""
Tests for discussion API permission logic
"""
import itertools

import ddt

from discussion_api.permissions import (
    can_delete,
    get_editable_fields,
    get_initializable_comment_fields,
    get_initializable_thread_fields,
)
from lms.lib.comment_client.comment import Comment
from lms.lib.comment_client.thread import Thread
from lms.lib.comment_client.user import User
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def _get_context(requester_id, is_requester_privileged, is_cohorted=False, thread=None):
    """Return a context suitable for testing the permissions module"""
    return {
        "cc_requester": User(id=requester_id),
        "is_requester_privileged": is_requester_privileged,
        "course": CourseFactory(cohort_config={"cohorted": is_cohorted}),
        "thread": thread,
    }


@ddt.ddt
class GetInitializableFieldsTest(ModuleStoreTestCase):
    """Tests for get_*_initializable_fields"""
    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_thread(self, is_privileged, is_cohorted):
        context = _get_context(
            requester_id="5",
            is_requester_privileged=is_privileged,
            is_cohorted=is_cohorted
        )
        actual = get_initializable_thread_fields(context)
        expected = {
            "abuse_flagged", "course_id", "following", "raw_body", "read", "title", "topic_id", "type", "voted"
        }
        if is_privileged and is_cohorted:
            expected |= {"group_id"}
        self.assertEqual(actual, expected)

    @ddt.data(*itertools.product([True, False], ["question", "discussion"], [True, False]))
    @ddt.unpack
    def test_comment(self, is_thread_author, thread_type, is_privileged):
        context = _get_context(
            requester_id="5",
            is_requester_privileged=is_privileged,
            thread=Thread(user_id="5" if is_thread_author else "6", thread_type=thread_type)
        )
        actual = get_initializable_comment_fields(context)
        expected = {
            "abuse_flagged", "parent_id", "raw_body", "thread_id", "voted"
        }
        if (is_thread_author and thread_type == "question") or is_privileged:
            expected |= {"endorsed"}
        self.assertEqual(actual, expected)


@ddt.ddt
class GetEditableFieldsTest(ModuleStoreTestCase):
    """Tests for get_editable_fields"""
    @ddt.data(*itertools.product([True, False], [True, False], [True, False]))
    @ddt.unpack
    def test_thread(self, is_author, is_privileged, is_cohorted):
        thread = Thread(user_id="5" if is_author else "6", type="thread")
        context = _get_context(
            requester_id="5",
            is_requester_privileged=is_privileged,
            is_cohorted=is_cohorted
        )
        actual = get_editable_fields(thread, context)
        expected = {"abuse_flagged", "following", "read", "voted"}
        if is_author or is_privileged:
            expected |= {"topic_id", "type", "title", "raw_body"}
        if is_privileged and is_cohorted:
            expected |= {"group_id"}
        self.assertEqual(actual, expected)

    @ddt.data(*itertools.product([True, False], [True, False], ["question", "discussion"], [True, False]))
    @ddt.unpack
    def test_comment(self, is_author, is_thread_author, thread_type, is_privileged):
        comment = Comment(user_id="5" if is_author else "6", type="comment")
        context = _get_context(
            requester_id="5",
            is_requester_privileged=is_privileged,
            thread=Thread(user_id="5" if is_thread_author else "6", thread_type=thread_type)
        )
        actual = get_editable_fields(comment, context)
        expected = {"abuse_flagged", "voted"}
        if is_author or is_privileged:
            expected |= {"raw_body"}
        if (is_thread_author and thread_type == "question") or is_privileged:
            expected |= {"endorsed"}
        self.assertEqual(actual, expected)


@ddt.ddt
class CanDeleteTest(ModuleStoreTestCase):
    """Tests for can_delete"""
    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_thread(self, is_author, is_privileged):
        thread = Thread(user_id="5" if is_author else "6")
        context = _get_context(requester_id="5", is_requester_privileged=is_privileged)
        self.assertEqual(can_delete(thread, context), is_author or is_privileged)

    @ddt.data(*itertools.product([True, False], [True, False], [True, False]))
    @ddt.unpack
    def test_comment(self, is_author, is_thread_author, is_privileged):
        comment = Comment(user_id="5" if is_author else "6")
        context = _get_context(
            requester_id="5",
            is_requester_privileged=is_privileged,
            thread=Thread(user_id="5" if is_thread_author else "6")
        )
        self.assertEqual(can_delete(comment, context), is_author or is_privileged)
