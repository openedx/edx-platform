"""
HTTP end-points for the Bookmarks API.

For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/Bookmarks+API
"""
from eventtracking import tracker
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _, ugettext_noop

from rest_framework import status
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.core.lib.api.permissions import IsUserInUrl
from openedx.core.lib.api.serializers import PaginationSerializer

from xmodule.modulestore.exceptions import ItemNotFoundError

from lms.djangoapps.lms_xblock.runtime import unquote_slashes

from . import DEFAULT_FIELDS, OPTIONAL_FIELDS, api
from .serializers import BookmarkSerializer

log = logging.getLogger(__name__)


class BookmarksViewMixin(object):
    """
    Shared code for bookmarks views.
    """

    def fields_to_return(self, params):
        """
        Returns names of fields which should be included in the response.

        Arguments:
            params (dict): The request parameters.
        """
        optional_fields = params.get('fields', '').split(',')
        return DEFAULT_FIELDS + [field for field in optional_fields if field in OPTIONAL_FIELDS]

    def error_response(self, message, error_status=status.HTTP_400_BAD_REQUEST):
        """
        Create and return a Response.

        Arguments:
            message (string): The message to put in the developer_message
                and user_message fields.
            status: The status of the response. Default is HTTP_400_BAD_REQUEST.
        """
        return Response(
            {
                "developer_message": message,
                "user_message": _(message)  # pylint: disable=translation-of-non-string
            },
            status=error_status
        )


class BookmarksListView(ListCreateAPIView, BookmarksViewMixin):
    """
    **Use Case**

        * Get a paginated list of bookmarks for a user.

            The list can be filtered by passing parameter "course_id=<course_id>"
            to only include bookmarks from a particular course.

            The bookmarks are always sorted in descending order by creation date.

            Each page in the list contains 10 bookmarks by default. The page
            size can be altered by passing parameter "page_size=<page_size>".

            To include the optional fields pass the values in "fields" parameter
            as a comma separated list. Possible values are:

                * "display_name"
                * "path"

        * Create a new bookmark for a user.

            The POST request only needs to contain one parameter "usage_id".

            Http400 is returned if the format of the request is not correct,
            the usage_id is invalid or a block corresponding to the usage_id
            could not be found.

    **Example Requests**

        GET /api/bookmarks/v1/bookmarks/?course_id={course_id1}&fields=display_name,path

        POST /api/bookmarks/v1/bookmarks/
        Request data: {"usage_id": <usage-id>}

    **Response Values**

        * count: The number of bookmarks in a course.

        * next: The URI to the next page of bookmarks.

        * previous: The URI to the previous page of bookmarks.

        * num_pages: The number of pages listing bookmarks.

        * results:  A list of bookmarks returned. Each collection in the list
          contains these fields.

            * id: String. The identifier string for the bookmark: {user_id},{usage_id}.

            * course_id: String. The identifier string of the bookmark's course.

            * usage_id: String. The identifier string of the bookmark's XBlock.

            * display_name: String. (optional) Display name of the XBlock.

            * path: List. (optional) List of dicts containing {"usage_id": <usage-id>, display_name:<display-name>}
                for the XBlocks from the top of the course tree till the parent of the bookmarked XBlock.

            * created: ISO 8601 String. The timestamp of bookmark's creation.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 10
    max_paginate_by = 500
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = BookmarkSerializer

    def get_serializer_context(self):
        """
        Return the context for the serializer.
        """
        context = super(BookmarksListView, self).get_serializer_context()
        if self.request.method == 'GET':
            context['fields'] = self.fields_to_return(self.request.QUERY_PARAMS)
        return context

    def get_queryset(self):
        """
        Returns queryset of bookmarks for GET requests.

        The results will only include bookmarks for the request's user.
        If the course_id is specified in the request parameters,
        the queryset will only include bookmarks from that course.
        """
        course_id = self.request.QUERY_PARAMS.get('course_id', None)

        if course_id:
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                log.error(u'Invalid course_id: %s.', course_id)
                return []
        else:
            course_key = None

        return api.get_bookmarks(user=self.request.user, course_key=course_key, serialized=False)

    def paginate_queryset(self, queryset, page_size=None):
        """ Override GenericAPIView.paginate_queryset for the purpose of eventing """
        page = super(BookmarksListView, self).paginate_queryset(queryset, page_size)

        course_id = self.request.QUERY_PARAMS.get('course_id')
        if course_id:
            try:
                CourseKey.from_string(course_id)
            except InvalidKeyError:
                return page

        event_data = {
            'list_type': 'all_courses',
            'bookmarks_count': page.paginator.count,
            'page_size': self.get_paginate_by(),
            'page_number': page.number,
        }
        if course_id is not None:
            event_data['list_type'] = 'per_course'
            event_data['course_id'] = course_id

        tracker.emit('edx.bookmark.listed', event_data)

        return page

    def post(self, request):
        """
        POST /api/bookmarks/v1/bookmarks/
        Request data: {"usage_id": "<usage-id>"}
        """
        if not request.DATA:
            return self.error_response(ugettext_noop(u'No data provided.'))

        usage_id = request.DATA.get('usage_id', None)
        if not usage_id:
            return self.error_response(ugettext_noop(u'Parameter usage_id not provided.'))

        try:
            usage_key = UsageKey.from_string(unquote_slashes(usage_id))
        except InvalidKeyError:
            error_message = ugettext_noop(u'Invalid usage_id: {usage_id}.').format(usage_id=usage_id)
            log.error(error_message)
            return self.error_response(error_message)

        try:
            bookmark = api.create_bookmark(user=self.request.user, usage_key=usage_key)
        except ItemNotFoundError:
            error_message = ugettext_noop(u'Block with usage_id: {usage_id} not found.').format(usage_id=usage_id)
            log.error(error_message)
            return self.error_response(error_message)

        return Response(bookmark, status=status.HTTP_201_CREATED)


class BookmarksDetailView(APIView, BookmarksViewMixin):
    """
    **Use Cases**

        Get or delete a specific bookmark for a user.

    **Example Requests**:

        GET /api/bookmarks/v1/bookmarks/{username},{usage_id}/?fields=display_name,path

        DELETE /api/bookmarks/v1/bookmarks/{username},{usage_id}/

    **Response for GET**

        Users can only delete their own bookmarks. If the bookmark_id does not belong
        to a requesting user's bookmark a Http404 is returned. Http404 will also be
        returned if the bookmark does not exist.

        * id: String. The identifier string for the bookmark: {user_id},{usage_id}.

        * course_id: String. The identifier string of the bookmark's course.

        * usage_id: String. The identifier string of the bookmark's XBlock.

        * display_name: (optional) String. Display name of the XBlock.

        * path: (optional) List of dicts containing {"usage_id": <usage-id>, display_name: <display-name>}
            for the XBlocks from the top of the course tree till the parent of the bookmarked XBlock.

        * created: ISO 8601 String. The timestamp of bookmark's creation.

    **Response for DELETE**

        Users can only delete their own bookmarks.

        A successful delete returns a 204 and no content.

        Users can only delete their own bookmarks. If the bookmark_id does not belong
        to a requesting user's bookmark a 404 is returned. 404 will also be returned
        if the bookmark does not exist.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, IsUserInUrl)

    serializer_class = BookmarkSerializer

    def get_usage_key_or_error_response(self, usage_id):
        """
        Create and return usage_key or error Response.

        Arguments:
            usage_id (string): The id of required block.
        """
        try:
            return UsageKey.from_string(usage_id)
        except InvalidKeyError:
            error_message = ugettext_noop(u'Invalid usage_id: {usage_id}.').format(usage_id=usage_id)
            log.error(error_message)
            return self.error_response(error_message, status.HTTP_404_NOT_FOUND)

    def get(self, request, username=None, usage_id=None):  # pylint: disable=unused-argument
        """
        GET /api/bookmarks/v1/bookmarks/{username},{usage_id}?fields=display_name,path
        """
        usage_key_or_response = self.get_usage_key_or_error_response(usage_id=usage_id)

        if isinstance(usage_key_or_response, Response):
            return usage_key_or_response

        try:
            bookmark_data = api.get_bookmark(
                user=request.user,
                usage_key=usage_key_or_response,
                fields=self.fields_to_return(request.QUERY_PARAMS)
            )
        except ObjectDoesNotExist:
            error_message = ugettext_noop(
                u'Bookmark with usage_id: {usage_id} does not exist.'
            ).format(usage_id=usage_id)
            log.error(error_message)
            return self.error_response(error_message, status.HTTP_404_NOT_FOUND)

        return Response(bookmark_data)

    def delete(self, request, username=None, usage_id=None):  # pylint: disable=unused-argument
        """
        DELETE /api/bookmarks/v1/bookmarks/{username},{usage_id}
        """
        usage_key_or_response = self.get_usage_key_or_error_response(usage_id=usage_id)

        if isinstance(usage_key_or_response, Response):
            return usage_key_or_response

        try:
            api.delete_bookmark(user=request.user, usage_key=usage_key_or_response)
        except ObjectDoesNotExist:
            error_message = ugettext_noop(
                u'Bookmark with usage_id: {usage_id} does not exist.'
            ).format(usage_id=usage_id)
            log.error(error_message)
            return self.error_response(error_message, status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
