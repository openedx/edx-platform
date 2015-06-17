"""
Tests for discussion API permission logic
"""
import itertools
from unittest import TestCase

import ddt

from discussion_api.permissions import can_delete, get_editable_fields
from lms.lib.comment_client.comment import Comment
from lms.lib.comment_client.thread import Thread
from lms.lib.comment_client.user import User


def _get_context(requester_id, is_requester_privileged, thread=None):
    """Return a context suitable for testing the permissions module"""
    return {
        "cc_requester": User(id=requester_id),
        "is_requester_privileged": is_requester_privileged,
        "thread": thread,
    }


@ddt.ddt
class GetEditableFieldsTest(TestCase):
    """Tests for get_editable_fields"""
    @ddt.data(*itertools.product([True, False], [True, False]))
    @ddt.unpack
    def test_thread(self, is_author, is_privileged):
        thread = Thread(user_id="5" if is_author else "6", type="thread")
        context = _get_context(requester_id="5", is_requester_privileged=is_privileged)
        actual = get_editable_fields(thread, context)
        expected = {"abuse_flagged", "following", "voted"}
        if is_author or is_privileged:
            expected |= {"topic_id", "type", "title", "raw_body"}
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
class CanDeleteTest(TestCase):
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
