"""Database models for content search"""

from __future__ import annotations

from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.django.models import LearningContextKeyField
from rest_framework.request import Request

from cms.djangoapps.contentstore.views.course import get_courses_accessible_to_user
from openedx.core.djangoapps.content_libraries.api import get_libraries_for_user


class SearchAccess(models.Model):
    """
    Stores a numeric ID for each ContextKey.

    We use this shorter ID instead of the full ContextKey when determining a user's access to search-indexed course and
    library content because:

    a) in some deployments, users may be granted access to more than 1_000 individual courses, and
    b) the search filter request is stored in the JWT, which is limited to 8Kib.
    """
    id = models.BigAutoField(
        primary_key=True,
        help_text=_(
            "Numeric ID for each Course / Library context. This ID will generally require fewer bits than the full "
            "LearningContextKey, allowing more courses and libraries to be represented in content search filters."
        ),
    )
    context_key = LearningContextKeyField(
        max_length=255, unique=True, null=False,
    )


def get_access_ids_for_request(request: Request) -> List[int]:
    """
    Returns the SearchAccess.id values that the user has read access to.
    """
    courses, _ = get_courses_accessible_to_user(request)
    course_clause = models.Q(context_key__in=[
        course.id for course in courses
    ])
    libraries = get_libraries_for_user(user=request.user)
    library_clause = models.Q(context_key__in=[
        lib.library_key for lib in libraries
    ])

    # Sort by descending access ID to simulate prioritizing the "most recently created context keys".
    return list(
        SearchAccess.objects.filter(
            course_clause | library_clause
        ).order_by('-id').values_list("id", flat=True)
    )
