import logging
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookmarks_api.models import Bookmark

log = logging.getLogger(__name__)


class BookmarksView(APIView):
    """
    List all bookmarks or create.
    """

    def get(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Get a list of all bookmarks.
        """
        params = self.request.QUERY_PARAMS.dict()

        if 'course_id' not in params:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        results = Bookmark.objects.filter(course_id=params['course_id'], user_id=params['user']).order_by('-created')

        return Response([result.as_dict() for result in results])

    def post(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Create a new bookmark.

        Returns 400 request if bad payload is sent or it was empty object.
        """
        if 'id' in self.request.DATA:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            bookmark = Bookmark.create(self.request.DATA)
            bookmark.full_clean()
        except ValidationError as error:
            log.debug(error, exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)

        bookmark.save()

        # location = reverse('api:v1:annotations_detail', kwargs={'annotation_id': bookmark.id})

        return Response(bookmark.as_dict(), status=status.HTTP_201_CREATED)

