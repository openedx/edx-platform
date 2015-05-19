"""
For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/Bookmarks+API
"""
import logging

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.translation import ugettext as _


from rest_framework import status
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView


from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from bookmarks.serializers import BookmarkSerializer
from openedx.core.lib.api.serializers import PaginationSerializer

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.django import modulestore

from .models import Bookmark
from .api import get_bookmark


log = logging.getLogger(__name__)


DEFAULT_FIELDS = ["id", "course_id", "usage_id", "created"]
OPTIONAL_FIELDS = ['display_name', 'path']


class BookmarksView(ListCreateAPIView):
    """
    **Use Case**

        Get a paginated list of bookmarks in particular course.
        Each page in the list can contain up to 30 bookmarks by default.

        Create/Post a new bookmark for particular Xblock.

    **Example Requests**

          GET /api/bookmarks/v0/bookmarks/?course_id={course_id1}

          POST /api/bookmarks/v0/bookmarks/?course_id={course_id1}

    **Response Values**

        * count: The number of bookmarks in a course.

        * next: The URI to the next page of bookmarks.

        * previous: The URI to the previous page of bookmarks.

        * num_pages: The number of pages listing bookmarks.

        * results:  A list of bookmarks returned. Each collection in the list
          contains these fields.

            * id: String. The identifier string for the bookmark": {user_id},{usage_id}.

            * course_id: String. The identifier string of the bookmark's course.

            * usage_id: String. The identifier string of the bookmark's XBlock.

            * display_name: (optional) String. Display name of the XBlock.

            * path: (optional) List of dicts containing {"usage_id": "", display_name:""} for the XBlocks
                from the top of the course tree till the parent of the bookmarked XBlock.

            * created: ISO 8601 String. The timestamp of bookmark's creation.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 30
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = BookmarkSerializer

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super(BookmarksView, self).get_serializer_context()
        if self.request.method == 'POST':
            return context
        optional_fields = self.request.QUERY_PARAMS.get('fields', [])
        optional_fields_list = optional_fields.split(',') if optional_fields else []
        context['fields'] = DEFAULT_FIELDS + [field for field in optional_fields_list if field in OPTIONAL_FIELDS]
        return context

    def get_queryset(self):
        course_id = self.request.QUERY_PARAMS.get('course_id', None)

        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Invalid course id '{course_id}'")
            return []

        results_queryset = Bookmark.objects.filter(course_key=course_key, user=self.request.user).order_by('-created')

        return results_queryset

    def post(self, request):
        """
        POST /api/bookmarks/v0/bookmarks/?course_id={course_id1}
        """
        if not request.DATA:
            error_message = _("No data provided")
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usage_id = request.DATA.get('usage_id', None)
        if not usage_id:
            error_message = _('No usage id provided')
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usage_key = UsageKey.from_string(usage_id)

            # usage_key's course_key may have an empty run property
            usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
            course_key = usage_key.course_key
        except InvalidKeyError as exception:
            return Response(
                {
                    "developer_message": exception.message,
                    "user_message": _(u"Invalid usage id")
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        bookmarks_data = {
            "usage_key": usage_key,
            "course_key": course_key,
            "user": request.user,
        }

        try:
            bookmark = Bookmark.create(bookmarks_data)
        except ItemNotFoundError as exception:
            return Response(
                {
                    "developer_message": exception.message,
                    "user_message": _(u"Invalid usage id")
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            BookmarkSerializer(bookmark).data,
            status=status.HTTP_201_CREATED
        )


class BookmarksDetailView(APIView):
    """
    **Use Cases**

        Get or Delete a specific bookmark.

    **Example Requests**:

        GET /api/bookmarks/v0/bookmarks/{username},{usage_id}?fields=path&display_name

        DELETE /api/bookmarks/v0/bookmarks/{username},{usage_id}?fields=path&display_name

    **Response Values for GET**
        Users can only delete their own bookmarks

        * id: String. The identifier string for the bookmark": {user_id},{usage_id}.

        * course_id: String. The identifier string of the bookmark's course.

        * usage_id: String. The identifier string of the bookmark's XBlock.

        * display_name: (optional) String. Display name of the XBlock.

        * path: (optional) List of dicts containing {"usage_id": "", display_name:""} for the XBlocks
            from the top of the course tree till the parent of the bookmarked XBlock.

        * created: ISO 8601 String. The timestamp of bookmark's creation.

    **Response for DELETE**

        A successful delete returns a 204 and no content.

        Users can only delete their own bookmarks. If the requesting user
        does not have username "username", this method will return with a
        status of 404.

        If the specified bookmark does not exist, this method returns a
        404.

    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = BookmarkSerializer

    def get(self, request, username=None, usage_id=None):
        """
        GET /api/bookmarks/v0/bookmarks/{username},{usage_id}?fields=path&display_name
        """
        if request.user.username != username:
            # Return a 404. If one user is looking up the other users.
            return Response(status=status.HTTP_404_NOT_FOUND)

        optional_fields = self.request.QUERY_PARAMS.get('fields', [])
        optional_fields = optional_fields.split(',') if optional_fields else []
        optional_fields_to_add = DEFAULT_FIELDS + [field for field in optional_fields if field in OPTIONAL_FIELDS]

        try:
            bookmarks_data = get_bookmark(request.user, usage_id, fields_to_add=optional_fields_to_add)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as exception:
            return Response(
                {
                    "developer_message": exception.message,
                    "user_message": _(u'The bookmark does not exist.')
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except InvalidKeyError as exception:
            return Response(
                {
                    "developer_message": exception.message,
                    "user_message": _(u"Invalid usage id")
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(bookmarks_data)

    def delete(self, request, username=None, usage_id=None):
        """
        DELETE /api/bookmarks/v0/bookmarks/{username},{usage_id}
        """
        if request.user.username != username:
            # Return a 404. If one user is looking up the other users.
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            bookmark = get_bookmark(request.user, usage_id, serialized=False)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as exception:
            return Response(
                {
                    "developer_message": exception.message,
                    "user_message": _(u'The bookmark does not exist.')
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except InvalidKeyError as exception:
            return Response(
                {
                    "developer_message": exception.message,
                    "user_message": _(u"Invalid usage id")
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        bookmark.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
