"""
Helper functions and classes for discussion tests.
"""

from uuid import uuid4

from ...fixtures.discussion import (
    SingleThreadViewFixture,
    Thread,
    Response,
)


class BaseDiscussionMixin(object):
    """
    A mixin containing methods common to discussion tests.
    """
    def setup_thread(self, num_responses, **thread_kwargs):
        """
        Create a test thread with the given number of responses, passing all
        keyword arguments through to the Thread fixture, then invoke
        setup_thread_page.
        """
        thread_id = "test_thread_{}".format(uuid4().hex)
        thread_fixture = SingleThreadViewFixture(
            Thread(id=thread_id, commentable_id=self.discussion_id, **thread_kwargs)
        )
        for i in range(num_responses):
            thread_fixture.addResponse(Response(id=str(i), body=str(i)))
        thread_fixture.push()
        self.setup_thread_page(thread_id)
