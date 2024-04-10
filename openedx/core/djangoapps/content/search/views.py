"""
REST API for content search
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
import meilisearch
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.djangoapps.student.role_helpers import get_course_roles
from common.djangoapps.student.roles import GlobalStaff
from openedx.core.lib.api.view_utils import view_auth_classes
from openedx.core.djangoapps.content.search.documents import STUDIO_INDEX_NAME
from openedx.core.djangoapps.content.search.models import get_access_ids_for_request

User = get_user_model()
log = logging.getLogger(__name__)
MAX_ACCESS_IDS_IN_FILTER = 1_000
MAX_ORGS_IN_FILTER = 1_000


def _get_meili_api_key_uid():
    """
    Helper method to get the UID of the API key we're using for Meilisearch
    """
    if not hasattr(_get_meili_api_key_uid, "uid"):
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
        _get_meili_api_key_uid.uid = client.get_key(settings.MEILISEARCH_API_KEY).uid
    return _get_meili_api_key_uid.uid


def _get_meili_access_filter(request: Request) -> dict:
    """
    Return meilisearch filter based on the requesting user's permissions.
    """
    # Global staff can see anything, so no filters required.
    if GlobalStaff().has_user(request.user):
        return {}

    # Everyone else is limited to their org staff roles...
    user_orgs = _get_user_orgs(request)[:MAX_ORGS_IN_FILTER]

    # ...or the N most recent courses and libraries they can access.
    access_ids = get_access_ids_for_request(request, omit_orgs=user_orgs)[:MAX_ACCESS_IDS_IN_FILTER]
    return {
        "filter": f"org IN {user_orgs} OR access_id IN {access_ids}",
    }


def _get_user_orgs(request: Request) -> list[str]:
    """
    Get the org.short_names for the organizations that the requesting user has OrgStaffRole or OrgInstructorRole.

    Note: org-level roles have course_id=None to distinguish them from course-level roles.
    """
    course_roles = get_course_roles(request.user)
    return list(set(
        role.org
        for role in course_roles
        if role.course_id is None and role.role in ['staff', 'instructor']
    ))


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
        client = meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_API_KEY)
        index_name = settings.MEILISEARCH_INDEX_PREFIX + STUDIO_INDEX_NAME

        # Create an API key that only allows the user to search content that they have permission to view:
        expires_at = datetime.now(tz=timezone.utc) + timedelta(days=7)
        search_rules = {
            index_name: _get_meili_access_filter(request),
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
