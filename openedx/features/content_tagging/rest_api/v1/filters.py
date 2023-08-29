"""
API Filters for content tagging org
"""

from rest_framework.filters import BaseFilterBackend

from ...rules import is_taxonomy_admin


class UserOrgFilterBackend(BaseFilterBackend):
    """
    Taxonomy admin can see all taxonomies
    Everyone else can see only enabled taxonomies

    """

    def filter_queryset(self, request, queryset, _):
        if is_taxonomy_admin(request.user):
            return queryset

        return queryset.filter(enabled=True)
