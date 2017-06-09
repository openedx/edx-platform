"""
Discussion API views
"""
from django.core.exceptions import ValidationError
from rest_framework.exceptions import UnsupportedMediaType
from rest_framework.parsers import JSONParser

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from discussion_api.api import (
    create_comment,
    create_thread,
    delete_thread,
    delete_comment,
    get_comment_list,
    get_response_comments,
    get_course,
    get_course_topics,
    get_thread,
    get_thread_list,
    update_comment,
    update_thread,
)
from discussion_api.forms import CommentListGetForm, ThreadListGetForm, CommentGetForm
from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes


@view_auth_classes()
class CourseView(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Retrieve general discussion metadata for a course.

    **Example Requests**:

        GET /api/discussion/v1/courses/course-v1:ExampleX+Subject101+2015

    **Response Values**:

        * id: The identifier of the course

        * blackouts: A list of objects representing blackout periods (during
            which discussions are read-only except for privileged users). Each
            item in the list includes:

            * start: The ISO 8601 timestamp for the start of the blackout period

            * end: The ISO 8601 timestamp for the end of the blackout period

        * thread_list_url: The URL of the list of all threads in the course.

        * topics_url: The URL of the topic listing for the course.
    """
    def get(self, request, course_id):
        """Implements the GET method as described in the class docstring."""
        course_key = CourseKey.from_string(course_id)  # TODO: which class is right?
        return Response(get_course(request, course_key))


@view_auth_classes()
class CourseTopicsView(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**

        Retrieve the topic listing for a course. Only topics accessible to the
        authenticated user are included.

    **Example Requests**:

        GET /api/discussion/v1/course_topics/course-v1:ExampleX+Subject101+2015
            ?topic_id={topic_id_1, topid_id_2}

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
        """
        Implements the GET method as described in the class docstring.
        """
        course_key = CourseKey.from_string(course_id)
        topic_ids = self.request.GET.get('topic_id')
        with modulestore().bulk_operations(course_key):
            response = get_course_topics(
                request,
                course_key,
                set(topic_ids.strip(',').split(',')) if topic_ids else None,
            )
        return Response(response)


@view_auth_classes()
class ThreadViewSet(DeveloperErrorViewMixin, ViewSet):
    """
    **Use Cases**

        Retrieve the list of threads for a course, retrieve thread details,
        post a new thread, or modify or delete an existing thread.

    **Example Requests**:

        GET /api/discussion/v1/threads/?course_id=ExampleX/Demo/2015

        GET /api/discussion/v1/threads/{thread_id}

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
        Content Type: "application/merge-patch+json"

        DELETE /api/discussion/v1/threads/thread_id

    **GET Thread List Parameters**:

        * course_id (required): The course to retrieve threads for

        * page: The (1-indexed) page to retrieve (default is 1)

        * page_size: The number of items per page (default is 10, max is 100)

        * topic_id: The id of the topic to retrieve the threads. There can be
            multiple topic_id queries to retrieve threads from multiple topics
            at once.

        * text_search: A search string to match. Any thread whose content
            (including the bodies of comments in the thread) matches the search
            string will be returned.

        * order_by: Must be "last_activity_at", "comment_count", or
            "vote_count". The key to sort the threads by. The default is
            "last_activity_at".

        * order_direction: Must be "desc". The direction in which to sort the
            threads by. The default and only value is "desc". This will be
            removed in a future major version.

        * following: If true, retrieve only threads the requesting user is
            following

        * view: "unread" for threads the requesting user has not read, or
            "unanswered" for question threads with no marked answer. Only one
            can be selected.

        * requested_fields: (list) Indicates which additional fields to return
          for each thread. (supports 'profile_image')

        The topic_id, text_search, and following parameters are mutually
        exclusive (i.e. only one may be specified in a request)

    **GET Thread Parameters**:

        * thread_id (required): The id of the thread

        * requested_fields (optional parameter): (list) Indicates which additional
         fields to return for each thread. (supports 'profile_image')

    **POST Parameters**:

        * course_id (required): The course to create the thread in

        * topic_id (required): The topic to create the thread in

        * type (required): The thread's type (either "question" or "discussion")

        * title (required): The thread's title

        * raw_body (required): The thread's raw body text

        * following (optional): A boolean indicating whether the user should
            follow the thread upon its creation; defaults to false

    **PATCH Parameters**:

        * abuse_flagged (optional): A boolean to mark thread as abusive

        * voted (optional): A boolean to vote for thread

        * read (optional): A boolean to mark thread as read

        * topic_id, type, title, and raw_body are accepted with the same meaning
        as in a POST request

        If "application/merge-patch+json" is not the specified content type,
        a 415 error is returned.

    **GET Thread List Response Values**:

        * results: The list of threads; each item in the list has the same
            fields as the POST/PATCH response below

        * next: The URL of the next page (or null if first page)

        * previous: The URL of the previous page (or null if last page)

        * text_search_rewrite: The search string to which the text_search
            parameter was rewritten in order to match threads (e.g. for spelling
            correction)

    **GET Thread Details Response Values**:

        Same response fields as the POST/PATCH response below

    **POST/PATCH response values**:

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

        * editable_fields: The fields that the requesting user is allowed to
            modify with a PATCH request

        * read: Boolean indicating whether the user has read this thread

        * has_endorsed: Boolean indicating whether this thread has been answered

        * response_count: The number of direct responses for a thread

    **DELETE response values:

        No content is returned for a DELETE request

    """
    lookup_field = "thread_id"
    parser_classes = (JSONParser, MergePatchParser,)

    def list(self, request):
        """
        Implements the GET method for the list endpoint as described in the
        class docstring.
        """
        form = ThreadListGetForm(request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return get_thread_list(
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
            form.cleaned_data["requested_fields"]
        )

    def retrieve(self, request, thread_id=None):
        """
        Implements the GET method for thread ID
        """
        requested_fields = request.GET.get('requested_fields')
        return Response(get_thread(request, thread_id, requested_fields))

    def create(self, request):
        """
        Implements the POST method for the list endpoint as described in the
        class docstring.
        """
        return Response(create_thread(request, request.data))

    def partial_update(self, request, thread_id):
        """
        Implements the PATCH method for the instance endpoint as described in
        the class docstring.
        """
        if request.content_type != MergePatchParser.media_type:
            raise UnsupportedMediaType(request.content_type)
        return Response(update_thread(request, thread_id, request.data))

    def destroy(self, request, thread_id):
        """
        Implements the DELETE method for the instance endpoint as described in
        the class docstring
        """
        delete_thread(request, thread_id)
        return Response(status=204)


@view_auth_classes()
class CommentViewSet(DeveloperErrorViewMixin, ViewSet):
    """
    **Use Cases**

        Retrieve the list of comments in a thread, retrieve the list of
        child comments for a response comment, create a comment, or modify
        or delete an existing comment.

    **Example Requests**:

        GET /api/discussion/v1/comments/?thread_id=0123456789abcdef01234567

        GET /api/discussion/v1/comments/2123456789abcdef01234555

        POST /api/discussion/v1/comments/
        {
            "thread_id": "0123456789abcdef01234567",
            "raw_body": "Body text"
        }

        PATCH /api/discussion/v1/comments/comment_id
        {"raw_body": "Edited text"}
        Content Type: "application/merge-patch+json"

        DELETE /api/discussion/v1/comments/comment_id

    **GET Comment List Parameters**:

        * thread_id (required): The thread to retrieve comments for

        * endorsed: If specified, only retrieve the endorsed or non-endorsed
          comments accordingly. Required for a question thread, must be absent
          for a discussion thread.

        * page: The (1-indexed) page to retrieve (default is 1)

        * page_size: The number of items per page (default is 10, max is 100)

        * requested_fields: (list) Indicates which additional fields to return
          for each thread. (supports 'profile_image')

    **GET Child Comment List Parameters**:

        * comment_id (required): The comment to retrieve child comments for

        * page: The (1-indexed) page to retrieve (default is 1)

        * page_size: The number of items per page (default is 10, max is 100)

        * requested_fields: (list) Indicates which additional fields to return
          for each thread. (supports 'profile_image')


    **POST Parameters**:

        * thread_id (required): The thread to post the comment in

        * parent_id: The parent comment of the new comment. Can be null or
          omitted for a comment that should be directly under the thread

        * raw_body: The comment's raw body text

    **PATCH Parameters**:

        raw_body is accepted with the same meaning as in a POST request

        If "application/merge-patch+json" is not the specified content type,
        a 415 error is returned.

    **GET Response Values**:

        * results: The list of comments; each item in the list has the same
            fields as the POST response below

        * next: The URL of the next page (or null if first page)

        * previous: The URL of the previous page (or null if last page)

    **POST/PATCH Response Values**:

        * id: The id of the comment

        * thread_id: The id of the comment's thread

        * parent_id: The id of the comment's parent

        * author: The username of the comment's author, or None if the
          comment is anonymous

        * author_label: A label indicating whether the author has a special
          role in the course, either "Staff" for moderators and
          administrators or "Community TA" for community TAs

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

        * editable_fields: The fields that the requesting user is allowed to
            modify with a PATCH request

    **DELETE Response Value**

        No content is returned for a DELETE request

    """
    lookup_field = "comment_id"
    parser_classes = (JSONParser, MergePatchParser,)

    def list(self, request):
        """
        Implements the GET method for the list endpoint as described in the
        class docstring.
        """
        form = CommentListGetForm(request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return get_comment_list(
            request,
            form.cleaned_data["thread_id"],
            form.cleaned_data["endorsed"],
            form.cleaned_data["page"],
            form.cleaned_data["page_size"],
            form.cleaned_data["requested_fields"],
        )

    def retrieve(self, request, comment_id=None):
        """
        Implements the GET method for comments against response ID
        """
        form = CommentGetForm(request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)
        return get_response_comments(
            request,
            comment_id,
            form.cleaned_data["page"],
            form.cleaned_data["page_size"],
            form.cleaned_data["requested_fields"],
        )

    def create(self, request):
        """
        Implements the POST method for the list endpoint as described in the
        class docstring.
        """
        return Response(create_comment(request, request.data))

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
        if request.content_type != MergePatchParser.media_type:
            raise UnsupportedMediaType(request.content_type)
        return Response(update_comment(request, comment_id, request.data))
