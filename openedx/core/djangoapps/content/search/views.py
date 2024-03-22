"""
REST API for content search
"""
from datetime import datetime, timedelta, timezone
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
import meilisearch
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.roles import GlobalStaff
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.content.search.documents import STUDIO_INDEX_NAME

User = get_user_model()
log = logging.getLogger(__name__)


def _get_meili_api_key_uid():
    """
    Helper method to get the UID of the API key we're using for Meilisearch
    """
    if not hasattr(_get_meili_api_key_uid, "uid"):
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
        _get_meili_api_key_uid.uid = client.get_key(settings.MEILISEARCH_API_KEY).uid
    return _get_meili_api_key_uid.uid


@view_auth_classes(is_authenticated=True)
class StudioSearchView(APIView):
    """
    Give user details on how they can search studio content
    """

    def get(self, request):
        """
        Give user details on how they can search studio content
        """
        if not settings.MEILISEARCH_ENABLED:
            raise NotFound("Meilisearch features are not enabled.")
        if not GlobalStaff().has_user(request.user):
            # Until we enforce permissions properly (see below), this endpoint is restricted to global staff,
            # because it lets you search data from any course/library.
            raise PermissionDenied("For the moment, use of this search preview is restricted to global staff.")
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
        index_name = settings.MEILISEARCH_INDEX_PREFIX + STUDIO_INDEX_NAME

        # Create an API key that only allows the user to search content that they have permission to view:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=7)
        search_rules = {
            index_name: {
                # TODO: Apply filters here based on the user's permissions, so they can only search for content
                # that they have permission to view. Example:
                # 'filter': 'org = BradenX'
            }
        }
        # Note: the following is just generating a JWT. It doesn't actually make an API call to Meilisearch.
        restricted_api_key = client.generate_tenant_token(
            api_key_uid=_get_meili_api_key_uid(),
            search_rules=search_rules,
            expires_at=expires_at,
        )

        return Response({
            "url": settings.MEILISEARCH_PUBLIC_URL,
            "index_name": index_name,
            "api_key": restricted_api_key,
        })
