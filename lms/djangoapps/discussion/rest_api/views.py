"""
Discussion API views
"""


import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import CourseKey
from rest_framework import permissions, status
from rest_framework.exceptions import ParseError, UnsupportedMediaType
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from six import text_type

from lms.djangoapps.discussion.views import get_divided_discussions
from lms.djangoapps.instructor.access import update_forum_role
from lms.djangoapps.discussion.django_comment_client.utils import available_division_schemes
from lms.djangoapps.discussion.rest_api.api import (
    create_comment,
    create_thread,
    delete_comment,
    delete_thread,
    get_comment_list,
    get_course,
    get_course_topics,
    get_response_comments,
    get_thread,
    get_thread_list,
    update_comment,
    update_thread
)
from lms.djangoapps.discussion.rest_api.forms import (
    CommentGetForm,
    CommentListGetForm,
    CourseDiscussionRolesForm,
    CourseDiscussionSettingsForm,
    ThreadListGetForm
)
from lms.djangoapps.discussion.rest_api.serializers import (
    DiscussionRolesListSerializer,
    DiscussionRolesSerializer,
    DiscussionSettingsSerializer
)
from openedx.core.djangoapps.django_comment_common import comment_client
from openedx.core.djangoapps.django_comment_common.models import Role
from openedx.core.djangoapps.django_comment_common.utils import (
    get_course_discussion_settings,
    set_course_discussion_settings
)
from openedx.core.djangoapps.user_api.accounts.permissions import CanReplaceUsername, CanRetireUser
from openedx.core.djangoapps.user_api.models import UserRetirementStatus
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from openedx.core.lib.api.parsers import MergePatchParser
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import JsonResponse
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


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


class RetireUserView(APIView):
    """
    **Use Cases**

        A superuser or the user with the settings.RETIREMENT_SERVICE_WORKER_USERNAME
        can "retire" the user's data from the comments service, which will remove
        personal information and blank all posts / comments the user has made.

    **Example Requests**:
        POST /api/discussion/v1/retire_user/
        {
            "username": "an_original_user_name"
        }

    **Example Response**:
        Empty string
    """

    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanRetireUser)

    def post(self, request):
        """
        Implements the retirement endpoint.
        """
        username = request.data['username']

        try:
            retirement = UserRetirementStatus.get_retirement_for_retirement_action(username)
            cc_user = comment_client.User.from_django_user(retirement.user)

            # Send the retired username to the forums service, as the service cannot generate
            # the retired username itself. Forums users are referenced by Django auth_user id.
            cc_user.retire(retirement.retired_username)
        except UserRetirementStatus.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except comment_client.CommentClientRequestError as exc:
            # 404s from client service for users that don't exist there are expected
            # we can just pass those up.
            if exc.status_code == 404:
                return Response(status=status.HTTP_404_NOT_FOUND)
            raise
        except Exception as exc:  # pylint: disable=broad-except
            return Response(text_type(exc), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ReplaceUsernamesView(APIView):
    """
    WARNING: This API is only meant to be used as part of a larger job that
    updates usernames across all services. DO NOT run this alone or users will
    not match across the system and things will be broken.

    API will recieve a list of current usernames and their new username.

    POST /api/discussion/v1/accounts/replace_usernames/
        {
            "username_mappings": [
                {"current_username_1": "desired_username_1"},
                {"current_username_2": "desired_username_2"}
            ]
        }

    """

    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, CanReplaceUsername)

    def post(self, request):
        """
        Implements the username replacement endpoint
        """

        username_mappings = request.data.get("username_mappings")

        if not self._has_valid_schema(username_mappings):
            raise ParseError("Request data does not match schema")

        successful_replacements, failed_replacements = [], []

        for username_pair in username_mappings:
            current_username = list(username_pair.keys())[0]
            new_username = list(username_pair.values())[0]
            successfully_replaced = self._replace_username(current_username, new_username)
            if successfully_replaced:
                successful_replacements.append({current_username: new_username})
            else:
                failed_replacements.append({current_username: new_username})

        return Response(
            status=status.HTTP_200_OK,
            data={
                "successful_replacements": successful_replacements,
                "failed_replacements": failed_replacements
            }
        )

    def _replace_username(self, current_username, new_username):
        """
        Replaces the current username with the new username in the forums service
        """
        try:
            # This API will be called after the regular LMS API, so the username in
            # the DB will have already been updated to new_username
            current_user = User.objects.get(username=new_username)
            cc_user = comment_client.User.from_django_user(current_user)
            cc_user.replace_username(new_username)
        except User.DoesNotExist:
            log.warning(
                u"Unable to change username from %s to %s in forums because %s doesn't exist in LMS DB.",
                current_username,
                new_username,
                new_username,
            )
            return True
        except comment_client.CommentClientRequestError as exc:
            if exc.status_code == 404:
                log.info(
                    u"Unable to change username from %s to %s in forums because user doesn't exist in forums",
                    current_username,
                    new_username,
                )
                return True
            else:
                log.exception(
                    u"Unable to change username from %s to %s in forums because forums API call failed with: %s.",
                    current_username,
                    new_username,
                    exc,
                )
            return False

        log.info(
            u"Successfully changed username from %s to %s in forums.",
            current_username,
            new_username,
        )
        return True

    def _has_valid_schema(self, post_data):
        """ Verifies the data is a list of objects with a single key:value pair """
        if not isinstance(post_data, list):
            return False
        for obj in post_data:
            if not (isinstance(obj, dict) and len(obj) == 1):
                return False
        return True


class CourseDiscussionSettingsAPIView(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**
    Retrieve all the discussion settings for a course or update one or more of them.

    **Example Requests**

        GET /api/discussion/v1/courses/{course_id}/settings

        PATCH /api/discussion/v1/courses/{course_id}/settings
        {"always_divide_inline_discussions": true}

    **GET Discussion Settings Parameters**:

        * course_id (required): The course to retrieve the discussion settings for.

    **PATCH Discussion Settings Parameters**:

        * course_id (required): The course to retrieve the discussion settings for.

        The body should have the 'application/merge-patch+json' content type.

        * divided_inline_discussions: A list of IDs of the topics to be marked as divided inline discussions.

        * divided_course_wide_discussions: A list of IDs of the topics to be marked as divided course-wide discussions.

        * always_divide_inline_discussions: A boolean indicating whether inline discussions should always be
          divided or not.

        * division_scheme: A string corresponding to the division scheme to be used from the list of
          available division schemes.

    **GET and PATCH Discussion Settings Parameters Response Values**:

        A HTTP 404 Not Found response status code is returned when the requested course is invalid.

        A HTTP 400 Bad Request response status code is returned when the request is invalid.

        A HTTP 200 OK response status denote is returned to denote success.

        * id: The discussion settings id.

        * divided_inline_discussions: A list of divided inline discussions.

        * divided_course_wide_discussions: A list of divided course-wide discussions.

        * division_scheme: The division scheme used for the course discussions.

        * available_division_schemes: A list of available division schemes for the course.

    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    parser_classes = (JSONParser, MergePatchParser,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def _get_representation(self, course, course_key, discussion_settings):
        """
        Return a serialized representation of the course discussion settings.
        """
        divided_course_wide_discussions, divided_inline_discussions = get_divided_discussions(
            course, discussion_settings
        )
        return JsonResponse({
            'id': discussion_settings.id,
            'divided_inline_discussions': divided_inline_discussions,
            'divided_course_wide_discussions': divided_course_wide_discussions,
            'always_divide_inline_discussions': discussion_settings.always_divide_inline_discussions,
            'division_scheme': discussion_settings.division_scheme,
            'available_division_schemes': available_division_schemes(course_key)
        })

    def _get_request_kwargs(self, course_id):
        return dict(course_id=course_id)

    def get(self, request, course_id):
        """
        Implement a handler for the GET method.
        """
        kwargs = self._get_request_kwargs(course_id)
        form = CourseDiscussionSettingsForm(kwargs, request_user=request.user)

        if not form.is_valid():
            raise ValidationError(form.errors)

        course_key = form.cleaned_data['course_key']
        course = form.cleaned_data['course']
        discussion_settings = get_course_discussion_settings(course_key)
        return self._get_representation(course, course_key, discussion_settings)

    def patch(self, request, course_id):
        """
        Implement a handler for the PATCH method.
        """
        if request.content_type != MergePatchParser.media_type:
            raise UnsupportedMediaType(request.content_type)

        kwargs = self._get_request_kwargs(course_id)
        form = CourseDiscussionSettingsForm(kwargs, request_user=request.user)
        if not form.is_valid():
            raise ValidationError(form.errors)

        course = form.cleaned_data['course']
        course_key = form.cleaned_data['course_key']
        discussion_settings = get_course_discussion_settings(course_key)

        serializer = DiscussionSettingsSerializer(
            data=request.data,
            partial=True,
            course=course,
            discussion_settings=discussion_settings
        )
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        settings_to_change = serializer.validated_data['settings_to_change']

        try:
            discussion_settings = set_course_discussion_settings(course_key, **settings_to_change)
        except ValueError as e:
            raise ValidationError(text_type(e))

        return Response(status=status.HTTP_204_NO_CONTENT)


class CourseDiscussionRolesAPIView(DeveloperErrorViewMixin, APIView):
    """
    **Use Cases**
    Retrieve all the members of a given forum discussion role or update the membership of a role.

    **Example Requests**

        GET /api/discussion/v1/courses/{course_id}/roles/{rolename}

        POST /api/discussion/v1/courses/{course_id}/roles/{rolename}
        {"user_id": "<username or email>", "action": "<allow or revoke>"}

    **GET List Members of a Role Parameters**:

        * course_id (required): The course to which the role belongs to.

        * rolename (required): The name of the forum discussion role, the members of which have to be listed.
          Currently supported values are 'Moderator', 'Group Moderator', 'Community TA'. If the value has a space
          it has to be URL encoded.

    **POST Update the membership of a Role Parameters**:

        * course_id (required): The course to which the role belongs to.

        * rolename (required): The name of the forum discussion role, the members of which have to be listed.
          Currently supported values are 'Moderator', 'Group Moderator', 'Community TA'. If the value has a space
          it has to be URL encoded.

        The body can use either 'application/x-www-form-urlencoded' or 'application/json' content type.

        * user_id (required): The username or email address of the user whose membership has to be updated.

        * action (required): Either 'allow' or 'revoke', depending on the action to be performed on the membership.

    **GET and POST Response Values**:

        A HTTP 404 Not Found response status code is returned when the requested course is invalid.

        A HTTP 400 Bad Request response status code is returned when the request is invalid.

        A HTTP 200 OK response status denote is returned to denote success.

        * course_id: The course to which the role belongs to.

        * results: A list of the members belonging to the specified role.

            * username: Username of the user.

            * email: Email address of the user.

            * first_name: First name of the user.

            * last_name: Last name of the user.

            * group_name: Name of the group the user belongs to.

        * division_scheme: The division scheme used by the course.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def _get_request_kwargs(self, course_id, rolename):
        return dict(course_id=course_id, rolename=rolename)

    def get(self, request, course_id, rolename):
        """
        Implement a handler for the GET method.
        """
        kwargs = self._get_request_kwargs(course_id, rolename)
        form = CourseDiscussionRolesForm(kwargs, request_user=request.user)

        if not form.is_valid():
            raise ValidationError(form.errors)

        course_id = form.cleaned_data['course_key']
        role = form.cleaned_data['role']

        data = {'course_id': course_id, 'users': role.users.all()}
        context = {'course_discussion_settings': get_course_discussion_settings(course_id)}

        serializer = DiscussionRolesListSerializer(data, context=context)
        return Response(serializer.data)

    def post(self, request, course_id, rolename):
        """
        Implement a handler for the POST method.
        """
        kwargs = self._get_request_kwargs(course_id, rolename)
        form = CourseDiscussionRolesForm(kwargs, request_user=request.user)
        if not form.is_valid():
            raise ValidationError(form.errors)

        course_id = form.cleaned_data['course_key']
        rolename = form.cleaned_data['rolename']

        serializer = DiscussionRolesSerializer(data=request.data)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        action = serializer.validated_data['action']
        user = serializer.validated_data['user']
        try:
            update_forum_role(course_id, user, rolename, action)
        except Role.DoesNotExist:
            raise ValidationError(u"Role '{}' does not exist".format(rolename))

        role = form.cleaned_data['role']
        data = {'course_id': course_id, 'users': role.users.all()}
        context = {'course_discussion_settings': get_course_discussion_settings(course_id)}
        serializer = DiscussionRolesListSerializer(data, context=context)
        return Response(serializer.data)
