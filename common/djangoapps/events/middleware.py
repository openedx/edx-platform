"""Extracts edX specific information from the request and adds it to the tracker context."""

from __future__ import absolute_import

from eventtracking import tracker
from eventtracking.django.middleware import failures_only_in_debug
from events import contexts

CONTEXT_NAME = 'edx.course'

class EventRequestContextMiddleware(object):
    """
    Extracts the following information from the request and adds it to the context:

    * course_id - the full course_id in the form "organization/course_name/course_run"
    * organization
    * course_name
    * course_run

    Note that all of these variables are set to '' if the course_id is not included in
    the URL.  Some events are course scoped, however, communicate the course_id via other
    non-URL-path means, those events should override this context with the appropriate value
    after it has been extracted but before the event is emitted.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Extract the course_id from the view arguments.
        """
        with failures_only_in_debug():
            context = contexts.course_context_from_id(view_kwargs.get('course_id', ''))
            tracker.get_tracker().enter_context(CONTEXT_NAME, context)

        return None

    def process_response(self, request, response):
        """
        Exit the context.  Note that this method may be called for requests that were
        not attached to views, so there will be cases when the context has not been
        added.  Its not ideal, but we simply ignore those cases.

        Effectively this method removes the context if it exists.
        """
        with failures_only_in_debug():
            try:
                tracker.get_tracker().exit_context(CONTEXT_NAME)
            except KeyError:
                # process_view is not called on every request, but
                # process_response is, so the context may not have been
                # entered.
                pass

        return response