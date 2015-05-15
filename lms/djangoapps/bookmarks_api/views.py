"""
For more information, see:
https://openedx.atlassian.net/wiki/display/TNL/Bookmarks+API
"""
import logging

from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
from django.utils.translation import ugettext as _
from django.http import Http404


from rest_framework.generics import ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.authentication import OAuth2Authentication, SessionAuthentication

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from bookmarks_api import serializers
from openedx.core.lib.api.serializers import PaginationSerializer

from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.django import modulestore

from .models import Bookmark
from student.models import User


log = logging.getLogger(__name__)


class BookmarksView(ListCreateAPIView):
    """
    List all bookmarks or create.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    paginate_by = 1000
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
    serializer_class = serializers.BookmarkSerializer

    def get_queryset(self):
        course_id = self.request.QUERY_PARAMS.get('course_id', None)

        if not course_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            log.error("Invalid course id '{course_id}'")
            return list()
        results = Bookmark.objects.filter(course_key=course_key, user__id=self.request.user.id).order_by('-created')

        return results

    def post(self, request):
        """
        Create a new bookmark.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if not request.DATA:
            error_message = _("No data provided for bookmark")
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        usage_id = request.DATA.get('usage_id', None)
        if not usage_id:
            error_message = _('No usage id provided for bookmark')
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
        except InvalidKeyError:
            error_message = _(u"invalid usage id '{usage_id}'".format(usage_id=usage_id))
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            module_item = modulestore().get_item(usage_key)

            parent = module_item.get_parent()
            location_path = []
            while parent is not None:
                display_name = parent.display_name if parent.display_name else _("(Unnamed)")
                location_path.append({"display_name": display_name, "usage_id": unicode(parent.location)})
                parent = parent.get_parent()
        except ItemNotFoundError:
            log.warn(
                "Invalid location for usage_id: {usage_id}".format(
                    usage_id=usage_id
                )
            )
            raise Http404

        path_list = location_path[:2] if location_path else list()
        path_list.reverse()
        bookmarks_dict = {
            "usage_key": usage_key,
            "course_key": course_key,
            "user": request.user,
            "display_name": module_item.display_name,
            "_path": path_list
        }
        try:
            bookmark = Bookmark.create(bookmarks_dict)
        except ValidationError as error:
            log.debug(error, exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(serializers.BookmarkSerializer(bookmark).data, status=status.HTTP_201_CREATED)


class BookmarksDetailView(APIView):
    """
    List all bookmarks or create.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    serializer_class = serializers.BookmarkSerializer

    def get(self, request, username=None, usage_key_string=None):
        """

        :return:
        """
        if request.user.username != username:
            # Return a 404. If one user is looking up the other users.
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            error_message = u'The user {} does not exist.'.format(username)
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usage_key = UsageKey.from_string(usage_key_string)

            # usage_key's course_key may have an empty run property
            usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
        except InvalidKeyError:
            error_message = _(u"invalid usage id '{usage_key_string}'".format(usage_key_string=usage_key_string))
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            bookmark = Bookmark.objects.get(usage_key=usage_key, user=user)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            error_message = u'The bookmark does not exist.'
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializers.BookmarkSerializer(bookmark).data)

    def delete(self, request, username=None, usage_key_string=None):
        """

        :return:
        """
        if request.user.username != username:
            # Return a 404. If one user is looking up the other users.
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            user = User.objects.get(username=username)
        except ObjectDoesNotExist:
            error_message = u'The user {} does not exist.'.format(username)
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            usage_key = UsageKey.from_string(usage_key_string)

            # usage_key's course_key may have an empty run property
            usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
        except InvalidKeyError:
            error_message = _(u"invalid usage id '{usage_key_string}'".format(usage_key_string=usage_key_string))
            return Response(
                {
                    "developer_message": error_message,
                    "user_message": error_message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            Bookmark.objects.get(usage_key=usage_key, user=user).delete()
        except ObjectDoesNotExist:
            return Response('Bookmark not found! No update performed.', status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
