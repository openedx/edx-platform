"""
For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/Bookmarks+API
"""
import logging

from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.utils.translation import ugettext as _


from rest_framework import status
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication
from rest_framework.generics import ListCreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView


from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from bookmarks import serializers
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
    List all bookmarks or create.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 30
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = serializers.BookmarkSerializer

    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super(BookmarksView, self).get_serializer_context()
        if self.request.method == 'POST':
            return context
        optional_fields = self.request.QUERY_PARAMS.get('fields', [])
        optional_fields_list = optional_fields.split(',') if optional_fields else []
        context['fields'] = DEFAULT_FIELDS + [field for field in optional_fields_list
                                                   if field in OPTIONAL_FIELDS]
        return context

    def get_queryset(self):
        course_id = self.request.QUERY_PARAMS.get('course_id', None)

        if not course_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Invalid course id '{course_id}'")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        results_queryset = Bookmark.objects.filter(course_key=course_key, user=self.request.user).order_by('-created')

        return results_queryset

    def post(self, request):
        """
        Create a new bookmark.

        Returns 400 request if bad payload is sent or it was empty object.
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
                    "user_message": _(u"Invalid usage id: '{usage_id}'".format(usage_id=usage_id))
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
                    "user_message": _(u"Invalid usage id: '{usage_id}'".format(usage_id=usage_id))
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            serializers.BookmarkSerializer(bookmark).data,
            status=status.HTTP_201_CREATED
        )


class BookmarksDetailView(APIView):
    """
    List all bookmarks or create.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = serializers.BookmarkSerializer

    def get(self, request, username=None, usage_id=None):
        """

        :return:
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
                    "user_message": _(u"Invalid usage id: '{usage_id}'".format(usage_id=usage_id))
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(bookmarks_data)

    def delete(self, request, username=None, usage_id=None):
        """

        :return:
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
                    "user_message": _(u"Invalid usage id: '{usage_id}'".format(usage_id=usage_id))
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        bookmark.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
