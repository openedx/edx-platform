"""
Discussion API views
"""
from django.core.exceptions import ValidationError

from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from opaque_keys.edx.locator import CourseLocator

from discussion_api.api import create_thread, get_comment_list, get_course_topics, get_thread_list
from discussion_api.forms import CommentListGetForm, ThreadListGetForm
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin


class _ViewMixin(object):
    """
    Mixin to provide common characteristics and utility functions for Discussion
    API views
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)


class CourseTopicsView(_ViewMixin, DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Retrieve the topic listing for a course. Only topics accessible to the
        authenticated user are included.

    **Example Requests**:

        GET /api/discussion/v1/course_topics/{course_id}

    **Response Values**:

        * courseware_topics: The list of topic trees for courseware-linked
          topics. Each item in the list includes:

            * id: The id of the discussion topic (null for a topic that only
              has children but cannot contain threads itself).

            * name: The display name of the topic.

            * children: A list of child subtrees of the same format.

        * non_courseware_topics: The list of topic trees that are not linked to
              courseware. Items are of the same format as in courseware_topics.
    """
    def get(self, request, course_id):
        """Implements the GET method as described in the class docstring."""
        course_key = CourseLocator.from_string(course_id)
        return Response(get_course_topics(course_key, request.user))


class ThreadViewSet(_ViewMixin, DeveloperErrorViewMixin, ViewSet):
    """
    **Use Cases**

        Retrieve the list of threads for a course or post a new thread.

    **Example Requests**:

        GET /api/discussion/v1/threads/?course_id=ExampleX/Demo/2015

        POST /api/discussion/v1/threads
        {
          "course_id": "foo/bar/baz",
          "topic_id": "quux",
          "type": "discussion",
          "title": "Title text",
          "body": "Body text"
        }

    **GET Parameters**:

        * course_id (required): The course to retrieve threads for

        * page: The (1-indexed) page to retrieve (default is 1)

        * page_size: The number of items per page (default is 10, max is 100)

    **POST Parameters**:

        * course_id (required): The course to create the thread in

        * topic_id (required): The topic to create the thread in

        * type (required): The thread's type (either "question" or "discussion")

        * title (required): The thread's title

        * raw_body (required): The thread's raw body text

    **GET Response Values**:

        * results: The list of threads; each item in the list has the same
            fields as the POST response below

        * next: The URL of the next page (or null if first page)

        * previous: The URL of the previous page (or null if last page)

    **POST response values**:

        * id: The id of the thread

        * course_id: The id of the thread's course

        * topic_id: The id of the thread's topic

        * created_at: The ISO 8601 timestamp for the creation of the thread

        * updated_at: The ISO 8601 timestamp for the last modification of
            the thread, which may not have been an update of the title/body

        * type: The thread's type (either "question" or "discussion")

        * title: The thread's title

        * raw_body: The thread's raw body text without any rendering applied

        * pinned: Boolean indicating whether the thread has been pinned

        * closed: Boolean indicating whether the thread has been closed

        * comment_count: The number of comments within the thread

        * unread_comment_count: The number of comments within the thread
            that were created or updated since the last time the user read
            the thread

    """
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
                form.cleaned_data["page_size"]
            )
        )

    def create(self, request):
        """
        Implements the POST method for the list endpoint as described in the
        class docstring.
        """
        return Response(create_thread(request, request.DATA))


class CommentViewSet(_ViewMixin, DeveloperErrorViewMixin, ViewSet):
    """
    **Use Cases**

        Retrieve the list of comments in a thread.

    **Example Requests**:

        GET /api/discussion/v1/comments/?thread_id=0123456789abcdef01234567

    **GET Parameters**:

        * thread_id (required): The thread to retrieve comments for

        * endorsed: If specified, only retrieve the endorsed or non-endorsed
          comments accordingly. Required for a question thread, must be absent
          for a discussion thread.

        * page: The (1-indexed) page to retrieve (default is 1)

        * page_size: The number of items per page (default is 10, max is 100)

    **Response Values**:

        * results: The list of comments. Each item in the list includes:

            * id: The id of the comment

            * thread_id: The id of the comment's thread

            * parent_id: The id of the comment's parent

            * author: The username of the comment's author, or None if the
              comment is anonymous

            * author_label: A label indicating whether the author has a special
              role in the course, either "staff" for moderators and
              administrators or "community_ta" for community TAs

            * created_at: The ISO 8601 timestamp for the creation of the comment

            * updated_at: The ISO 8601 timestamp for the last modification of
                the comment, which may not have been an update of the body

            * raw_body: The comment's raw body text without any rendering applied

            * endorsed: Boolean indicating whether the comment has been endorsed
                (by a privileged user or, for a question thread, the thread
                author)

            * endorsed_by: The username of the endorsing user, if available

            * endorsed_by_label: A label indicating whether the endorsing user
                has a special role in the course (see author_label)

            * endorsed_at: The ISO 8601 timestamp for the endorsement, if
                available

            * abuse_flagged: Boolean indicating whether the requesting user has
              flagged the comment for abuse

            * voted: Boolean indicating whether the requesting user has voted
              for the comment

            * vote_count: The number of votes for the comment

            * children: The list of child comments (with the same format)

        * next: The URL of the next page (or null if first page)

        * previous: The URL of the previous page (or null if last page)
    """
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
                form.cleaned_data["page_size"]
            )
        )
