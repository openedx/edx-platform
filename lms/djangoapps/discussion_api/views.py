"""
Discussion API views
"""
from django.core.exceptions import ValidationError

from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from opaque_keys.edx.keys import CourseKey

from discussion_api.api import (
    create_comment,
    create_thread,
    delete_thread,
    delete_comment,
    get_comment_list,
    get_course,
    get_course_topics,
    get_thread_list,
    update_comment,
    update_thread,
)
from discussion_api.forms import CommentListGetForm, ThreadListGetForm
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin


class _ViewMixin(object):
    """
    Mixin to provide common characteristics and utility functions for Discussion
    API views
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class CourseView(_ViewMixin, DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Retrieve general discussion metadata for a course.

    **Example Requests**

        GET /api/discussion/v1/courses/{course_id}

    **Response Values**

        * id: The unique identifier for the course.

        * blackouts: A list of objects that represent any defined blackout
          periods during the course run. Discussions are read-only during a
          blackout period, except for users who have privileged discussion
          moderation roles in the course. Each item in the list includes the
          following values.

            * end: The ISO 8601 timestamp for the end of the blackout period.

            * start: The ISO 8601 timestamp for the start of the blackout
              period.

        * following_thread_list_url: The URL of the list of threads that the
          requesting user is following.

        * thread_list_url: The URL of the list of all discussion threads in
          the course.

        * topics_url: The URL of the list of discussion topics in the course.
    """
    def get(self, request, course_id):
        """Implements the GET method as described in the class docstring."""
        course_key = CourseKey.from_string(course_id)  # TODO: which class is right?
        return Response(get_course(request, course_key))


class CourseTopicsView(_ViewMixin, DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Retrieve the list of discussion topics for a course. Only topics that
        are accessible to the authenticated user are included: cohort
        assignments, content groups, release dates, and other access
        controls can affect access to content.

    **Example Requests**

        GET /api/discussion/v1/course_topics/{course_id}

    **Response Values**

        * courseware_topics: The list of topic trees for the content-specific
          discussion topics in the course. In Studio, course teams use
          discussion components to add content-specific discussion topics which
          are classified by category and identified by display name. The array
          includes a separate object for each category.

          Each item in the list includes the following values.

          * children: An array of child subtrees, with a separate object for
            each defined discussion category. For each category, includes an
            array with values to identify the ids, display names, and
            thread_list_urls for the discussion topics in that category. The
            children value is present, but null, for the individual topics
            within a category.

          * id: The internal ID assigned to the discussion topic. The ID is
            null for a topic that only has children but cannot contain
            threads itself.

          * name: The category name defined for the discussion topic or
            topics.

          * thread_list_url: The URL of the list of all discussion threads
            in the category.

        * non_courseware_topics: The list of topic trees for the course-wide
          discussion topics defined for the course. In Studio, course teams add
          course-wide discussion topics on the Advanced Settings page. Each item
          in the list includes the same values as for courseware_topics.
    """
    def get(self, request, course_id):
        """Implements the GET method as described in the class docstring."""
        course_key = CourseKey.from_string(course_id)
        return Response(get_course_topics(request, course_key))


class ThreadViewSet(_ViewMixin, DeveloperErrorViewMixin, ViewSet):
    """
    **Use Cases**

        Retrieve the list of threads for a course, post a new thread, or modify
        or delete an existing thread.

    **Example Requests**

        GET /api/discussion/v1/threads/?course_id={course_id}

        POST /api/discussion/v1/threads
        {
          "course_id": "foo/bar/baz",
          "topic_id": "quux",
          "type": "discussion",
          "title": "Title text",
          "raw_body": "Body text"
        }

        PATCH /api/discussion/v1/threads/thread_id
        {"raw_body": "Edited text"}

        DELETE /api/discussion/v1/threads/{thread_id}

    **GET Parameters**

        * course_id (required): The ID of the course to retrieve threads for.

        * following: Boolean. If true, retrieves only threads that the
          requesting user is following.

        * order_by: The key to use for sorting retrieved threads. Must be
          "last_activity_at", "comment_count", or "vote_count". Defaults to
          "last_activity_at".

        * order_direction: The direction in which to order retrieved threads.
          Must be "asc" or "desc". Defaults to "desc".

        * page: The (1-indexed) page to retrieve. Defaults to 1.

        * page_size: The number of items per page. Defaults to 10, with a
          maximum of 100.

        * text_search: A search string to match. Retrieves any thread with
          content that matches the search string, including the bodies of
          comments in the thread.

        * topic_id: The ID of the discussion topic to retrieve threads for.
          Multiple topic_id queries can be defined to retrieve threads from
          multiple topics at once.

        * view: "unread" to retrieve threads that the requesting user has not
          read, or "unanswered" to retrieve question threads that do not have a
          marked answer. Only one view can be specified in a request.

        The topic_id, text_search, and following parameters are mutually
        exclusive. Only one can be specified in a request.

    **POST Parameters**

        * course_id (required): The course to create the thread in.

        * following (optional): A Boolean that indicates whether the user will
          follow the thread upon its creation. Defaults to false.

        * raw_body (required): The text for the thread, without HTML markup.

        * title (required): The title for the thread.

        * topic_id (required): The discussion topic to create the thread in.

        * type (required): Specifies either "question" or "discussion" as the
          type of thread to create.

    **PATCH Parameters**

        topic_id, type, title, and raw_body are accepted with the same meaning
        as in a POST request.

        In addition, abuse_flagged, following, and voted are accepted.

    **GET Response Values**

        * next: The URL of the next page of results. Null for the last page.

        * previous: The URL of the previous page of results. Null for the first
          page.

        * results: An array that lists all of the returned threads. For each
          thread, an object contains the same set of values as in a POST/PATCH
          response, described below.

        * text_search_rewrite: If the search string in the text_search parameter
          was rewritten to match thread content, such as a spelling correction,
          contains the rewritten string.

    **POST/PATCH response values**

        * abuse_flagged: A Boolean that indicates whether the requesting user
          has flagged the thread for abuse.

        * author: The username of the thread's author. None if the thread is
          anonymous.

        * author_label: Indicates whether the author has a privileged role in
          the course. Discussion moderators and discussion administrators are
          identified as "staff" and community TAs are identified as
          "community_ta". Null for other users.

        * closed: A Boolean that indicates whether the thread has been closed.

        * comment_count: The number of comments within the thread.

        * comment_list_url: The URL of the list of all responses and comments to
          this thread.

        * course_id: The ID of the thread's course.

        * created_at: The ISO 8601 timestamp for the creation of the thread.

        * editable_fields: The fields that the requesting user is allowed to
          modify with a PATCH request: abuse_flagged, following, and voted.

        * endorsed_comment_list_url: For threads with a type of "question", the
          URL of the list of endorsed responses (if any).

        * following: A Boolean that indicates whether the requesting user is
          following the thread.

        * group_id: The ID of the cohort that can view and comment on this
          thread.

        * group_name: The name of the cohort that can view and comment on this
          thread.

        * has_endorsed: For threads with a type of "question", a Boolean that
          indicates whether this thread has any responses that are marked as
          answers.

        * id: The ID of the thread.

        * pinned: A Boolean that indicates whether the thread has been pinned.

        * raw_body: The text for the thread, without HTML markup.

        * read: A Boolean that indicates whether the user has read this thread.

        * rendered_body: The text for the thread, including HTML tags.

        * title: The title of the thread.

        * topic_id: The ID of the thread's topic.

        * type: The thread's type: either "question" or "discussion".

        * updated_at: The ISO 8601 timestamp for the last modification of the
          thread, which might be an edit to one of the editable_fields as well
          as the title or body.

        * unread_comment_count: The number of comments within the thread that
          were created or updated since the last time the user read the thread.

        * vote_count: The number of votes that the thread has received.

        * voted: A Boolean that indicates whether the requesting user has
          voted for the thread.

        * non_endorsed_comment_list_url: For threads with a type of "question",
          the URL of the list of responses that are not marked as correct (if
          any).

    **DELETE response values:

        No content is returned for a DELETE request.

    """
    lookup_field = "thread_id"

    def list(self, request):
        """
        Implements the GET method for the list endpoint as described in the
        class docstring.
        """
        form = ThreadListGetForm(request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return Response(
            get_thread_list(
                request,
                form.cleaned_data["course_id"],
                form.cleaned_data["page"],
                form.cleaned_data["page_size"],
                form.cleaned_data["topic_id"],
                form.cleaned_data["text_search"],
                form.cleaned_data["following"],
                form.cleaned_data["view"],
                form.cleaned_data["order_by"],
                form.cleaned_data["order_direction"],
            )
        )

    def create(self, request):
        """
        Implements the POST method for the list endpoint as described in the
        class docstring.
        """
        return Response(create_thread(request, request.DATA))

    def partial_update(self, request, thread_id):
        """
        Implements the PATCH method for the instance endpoint as described in
        the class docstring.
        """
        return Response(update_thread(request, thread_id, request.DATA))

    def destroy(self, request, thread_id):
        """
        Implements the DELETE method for the instance endpoint as described in
        the class docstring
        """
        delete_thread(request, thread_id)
        return Response(status=204)


class CommentViewSet(_ViewMixin, DeveloperErrorViewMixin, ViewSet):
    """
    **Use Cases**

        Retrieve the list of comments in a thread, create a comment, or modify
        or delete an existing comment. In the two-level hierarchy of threads and
        comments that is currently used, comments include both the initial
        responses to a thread and comments on those responses.

    **Example Requests**

        GET /api/discussion/v1/comments/?thread_id=0123456789abcdef01234567

        POST /api/discussion/v1/comments/
        {
            "thread_id": "0123456789abcdef01234567",
            "raw_body": "Body text"
        }

        PATCH /api/discussion/v1/comments/comment_id
        {"raw_body": "Edited text"}

        DELETE /api/discussion/v1/comments/comment_id

    **GET Parameters**

        * endorsed: If specified as true, retrieves only comments that are
          marked as answers to the question. If false, retrieves only comments
          that are not endorsed as answers. Only applies to question threads,
          must be null for discussion threads.

        * mark_as_read: Marks the thread of the comments as read. Defaults to 
          False.

        * page: The (1-indexed) page to retrieve. Defaults to 1.

        * page_size: The number of items per page. Defaults to 10, with a
          maximum of 100.

    **POST Parameters**

        * parent_id: The parent comment of the new comment. If null or omitted,
          the comment is posted as a response, directly under the thread.

        * raw_body: The text for the comment, without HTML markup.

        * thread_id (required): The ID of the thread to post the comment in.

    **PATCH Parameters**

        raw_body is accepted with the same meaning as in a POST request.

    **GET Response Values**

        * next: The URL of the next page of results. Null for the last page.

        * previous: The URL of the previous page of results. Null for the first
          page.

        * results: An array that lists all of the returned comments. For each
          comment, an object contains the same set of values as in a POST/PATCH
          response, described below.

    **POST/PATCH Response Values**

        * abuse_flagged: A Boolean that indicates whether the requesting user has
          flagged the comment for abuse.

        * author: The username of the comment's author. None if the comment is
          anonymous.

        * author_label: Indicates whether the author has a privileged role in
          the course. Discussion moderators and discussion administrators are
          identified as "staff" and community TAs are identified as
          "community_ta". Null for other users.

        * children: An array that lists all of the child comments for this
          comment. For each comment, an object contains the same set of values
          as for the parent comment.

        * created_at: The ISO 8601 timestamp for the creation of the comment.

        * editable_fields: The fields that the requesting user is allowed to
          modify with a PATCH request: abuse_flagged and voted.

        * endorsed: A Boolean that indicates whether the comment is marked as the
          answer to a question by either the thread author or by a privileged
          user.

        * endorsed_at: The ISO 8601 timestamp for the endorsement, if available.

        * endorsed_by: The username of the endorsing user, if available.

        * endorsed_by_label: Indicates whether the endorsing user has a
          privileged role in the course. The values are the same as for
          author_label.

        * id: The ID of the comment.

        * parent_id: The ID of the parent comment that the comment was made to.
          Null for a comment that is posted directly under the thread.

        * raw_body: The text for the comment, without HTML markup.

        * rendered_body: The text for the comment, including HTML tags.

        * thread_id: The ID of the thread the comment was made to.

        * updated_at: The ISO 8601 timestamp for the last modification of the
          comment, which might be an edit to one of the editable_fields as well
          as the body.

        * vote_count: The number of votes that the comment has received.

        * voted: A Boolean that indicates whether the requesting user has voted
          for the comment.

    **DELETE Response Value**

        No content is returned for a DELETE request.

    """
    lookup_field = "comment_id"

    def list(self, request):
        """
        Implements the GET method for the list endpoint as described in the
        class docstring.
        """
        form = CommentListGetForm(request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return Response(
            get_comment_list(
                request,
                form.cleaned_data["thread_id"],
                form.cleaned_data["endorsed"],
                form.cleaned_data["page"],
                form.cleaned_data["page_size"],
                form.cleaned_data["mark_as_read"]
            )
        )

    def create(self, request):
        """
        Implements the POST method for the list endpoint as described in the
        class docstring.
        """
        return Response(create_comment(request, request.DATA))

    def destroy(self, request, comment_id):
        """
        Implements the DELETE method for the instance endpoint as described in
        the class docstring
        """
        delete_comment(request, comment_id)
        return Response(status=204)

    def partial_update(self, request, comment_id):
        """
        Implements the PATCH method for the instance endpoint as described in
        the class docstring.
        """
        return Response(update_comment(request, comment_id, request.DATA))
