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

    **Example Requests**:

        GET /api/discussion/v1/courses/{course_id}

    **Response Values**:

        * id: The unique identifier for the course.

        * blackouts: A list of objects that represent any defined blackout
          periods during the course run. Discussions are read-only during a
          blackout period, except for users who have privileged discussion
          moderation roles in the course. Each item in the list includes the
          following values.

            * start: The ISO 8601 timestamp for the start of the blackout
              period.

            * end: The ISO 8601 timestamp for the end of the blackout period.

        * following_thread_list_url: TBD

        * thread_list_url: The URL of the list of all discussion threads, or
          posts, in the course.

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

    **Example Requests**:

        GET /api/discussion/v1/course_topics/{course_id}

    **Response Values**:

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

            * id: The internal id assigned to the discussion topic. The id is
              null for a topic that only has children but cannot contain
              threads, or posts, itself.

            * name: The category name defined for the discussion topic or
              topics.

            * thread_list_url: The URL of the list of all discussion threads, or
              posts, in the category.

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

    **Example Requests**:

        GET /api/discussion/v1/threads/?course_id=ExampleX/Demo/2015

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

        DELETE /api/discussion/v1/threads/thread_id

    **GET Parameters**:

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

    **POST Parameters**:

        * course_id (required): The course to create the thread in.

        * topic_id (required): The discussion topic to create the thread in.

        * type (required): Specifies either "question" or "discussion" as the
          type of thread to create.

        * title (required): The title for the thread.

        * raw_body (required): The text for the thread, without HTML markup.

        * following (optional): A Boolean that indicates whether the user will
          follow the thread upon its creation. Defaults to false.

    **PATCH Parameters**:

        topic_id, type, title, and raw_body are accepted with the same meaning
        as in a POST request.

    **GET Response Values**:

        * next: The URL of the next page of results. Null for the last page.

        * previous: The URL of the previous page of results. Null for the first
          page.

        * results: An array that lists all of the returned threads. For each
          thread, an object contains the same set of values as in a POST/PATCH
          response, described below.

        * text_search_rewrite: If the search string in the text_search parameter
          was rewritten to match thread content, such as a spelling correction,
          contains the rewritten string.

    **POST/PATCH response values**:

        * author: The username of the thread's author. None if the thread is
          anonymous.

        * author_label: Indicates whether the author has a privileged role in
          the course. Discussion moderators and discussion administrators are
          identified as "staff" and community TAs are identified as
          "community_ta". Null for other users.

        * created_at: The ISO 8601 timestamp for the creation of the thread.

        * updated_at: The ISO 8601 timestamp for the last modification of the
          thread, which might be an edit to one of the editable_fields as well
          as the title or body.

        * raw_body: The text for the thread, without HTML markup.

        * rendered_body: The text for the thread, including HTML tags.

        * abuse_flagged: Boolean that indicates whether the requesting user has
          flagged the thread for abuse.

        * voted: Boolean that indicates whether the requesting user has voted
          for the thread.

        * vote_count: The number of votes that the thread has received.

        * editable_fields: The fields that the requesting user is allowed to
          modify with a PATCH request: abuse_flagged, following, and voted.

        * course_id: The id of the thread's course.

        * topic_id: The id of the thread's topic.

        * group_id: TBD

        * group_name: TBD

        * title: The thread's title.

        * pinned: Boolean that indicates whether the thread has been pinned.

        * closed: Boolean that indicates whether the thread has been closed.

        * following (optional): Boolean that indicates whether the requesting
          user is following the thread.

        * comment_count: The number of comments within the thread.

        * unread_comment_count: The number of comments within the thread that
          were created or updated since the last time the user read the thread.

        * comment_list_url: The URL of the list of all responses and comments to
          this thread.

        * endorsed_comment_list_url: For threads with a type of "question", the
          URL of the list of endorsed responses (if any).

        * non_endorsed_comment_list_url: For threads with a type of "question",
          the URL of the list of responses that are not marked as correct (if
          any).

        * read: Boolean that indicates whether the user has read this thread.

        * has_endorsed: For threads with a type of "question", Boolean that
          indicates whether this thread has any responses that are marked as
          answers.

        * id: The id of the thread.

        * type: The thread's type: either "question" or "discussion".

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

    **Example Requests**:

        GET /api/discussion/v1/comments/?thread_id=0123456789abcdef01234567

        POST /api/discussion/v1/comments/
        {
            "thread_id": "0123456789abcdef01234567",
            "raw_body": "Body text"
        }

        PATCH /api/discussion/v1/comments/comment_id
        {"raw_body": "Edited text"}

        DELETE /api/discussion/v1/comments/comment_id

    **GET Parameters**:

        * thread_id (required): The ID of the thread to retrieve comments for.

        * endorsed: If specified, retrieves only comments that have been marked
          as answering the question or that have been left unendorsed. Required
          for a question thread, must be absent for a discussion thread.

        * page: The (1-indexed) page to retrieve. Defaults to 1.

        * page_size: The number of items per page. Defaults to 10, with a
          maximum of 100.

        * mark_as_read: Will mark the thread of the comments as read. (default
            is False)

    **POST Parameters**:

        * thread_id (required): The thread to post the comment in.

        * parent_id: The parent comment of the new comment. If null or omitted,
          the comment is posted as a response, directly under the thread.

        * raw_body: The text for the comment, without HTML markup.

    **PATCH Parameters**:

        raw_body is accepted with the same meaning as in a POST request.

    **GET Response Values**:

        * results: An array that lists all of the returned comments. For each
          comment, an object contains the same set of values as in a POST/PATCH
          response, described below.

        * next: The URL of the next page of results. Null for the last page.

        * previous: The URL of the previous page of results. Null for the first
          page.

    **POST/PATCH Response Values**:

        * author: The username of the comment's author. None if the comment is
          anonymous.

        * author_label: Indicates whether the author has a privileged role in
          the course. Discussion moderators and discussion administrators are
          identified as "staff" and community TAs are identified as
          "community_ta". Null for other users.

        * created_at: The ISO 8601 timestamp for the creation of the comment.

        * updated_at: The ISO 8601 timestamp for the last modification of the
          comment, which might be an edit to one of the editable_fields as well
          as the body.

        * raw_body: The text for the comment, without HTML markup.

        * rendered_body: The text for the comment, including HTML tags.

        * abuse_flagged: Boolean that indicates whether the requesting user has
          flagged the comment for abuse.

        * voted: Boolean that indicates whether the requesting user has voted
          for the comment.

        * vote_count: The number of votes that the comment has received.

        * editable_fields: The fields that the requesting user is allowed to
          modify with a PATCH request: abuse_flagged and voted.

        * thread_id: The ID of the thread the comment was made to.

        * parent_id: The ID of the parent comment that the comment was made to.
          Null for a comment that is posted directly under the thread.

        * endorsed: Boolean that indicates whether the comment is marked as the
          answer to a question by either the thread author or by a privileged
          user.

        * endorsed_by: The username of the endorsing user, if available.

        * endorsed_by_label: Indicates whether the endorsing user has a
          privileged role in the course. The values are the same as for
          author_label.

        * endorsed_at: The ISO 8601 timestamp for the endorsement, if available.

        * children: An array that lists all of the child comments for this
          comment. For each comment, an object contains the same set of values
          as for the parent comment.

        * id: The id of the comment.

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
