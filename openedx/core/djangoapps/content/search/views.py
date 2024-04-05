"""
REST API for content search
"""
import logging

from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.roles import GlobalStaff
from openedx.core.lib.api.view_utils import view_auth_classes

from . import api

User = get_user_model()
log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class StudioSearchView(APIView):
    """
    Give user details on how they can search studio content
    """

    def get(self, request):
        """
        Give user details on how they can search studio content
        """
        if not api.is_meilisearch_enabled():
            raise NotFound("Meilisearch features are not enabled.")
        if not GlobalStaff().has_user(request.user):
            # Until we enforce permissions properly (see below), this endpoint is restricted to global staff,
            # because it lets you search data from any course/library.
            raise PermissionDenied("For the moment, use of this search preview is restricted to global staff.")

        response_data = api.generate_user_token_for_studio_search(request.user)

        return Response(response_data)
