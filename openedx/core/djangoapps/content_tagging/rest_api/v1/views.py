"""
Tagging Org API Views
"""

from openedx_tagging.core.tagging.rest_api.v1.views import TaxonomyView


from ...api import (
    create_taxonomy,
    get_taxonomies,
    get_taxonomies_for_org,
)
from .serializers import TaxonomyOrgListQueryParamsSerializer
from .filters import UserOrgFilterBackend


class TaxonomyOrgView(TaxonomyView):
    """
    View to list, create, retrieve, update, or delete Taxonomies.
    This view extends the TaxonomyView to add Organization filters.

    Refer to TaxonomyView docstring for usage details.

    **Additional List Query Parameters**
        * org (optional) - Filter by organization.

    **List Example Requests**
        GET api/content_tagging/v1/taxonomies?org=orgA                 - Get all taxonomies for organization A
        GET api/content_tagging/v1/taxonomies?org=orgA&enabled=true    - Get all enabled taxonomies for organization A

    **List Query Returns**
        * 200 - Success
        * 400 - Invalid query parameter
        * 403 - Permission denied
    """

    filter_backends = [UserOrgFilterBackend]

    def get_queryset(self):
        """
        Return a list of taxonomies.

        Returns all taxonomies by default.
        If you want the disabled taxonomies, pass enabled=False.
        If you want the enabled taxonomies, pass enabled=True.
        """
        query_params = TaxonomyOrgListQueryParamsSerializer(data=self.request.query_params.dict())
        query_params.is_valid(raise_exception=True)
        enabled = query_params.validated_data.get("enabled", None)
        org = query_params.validated_data.get("org", None)
        if org:
            return get_taxonomies_for_org(enabled, org)
        else:
            return get_taxonomies(enabled)

    def perform_create(self, serializer):
        """
        Create a new taxonomy.
        """
        serializer.instance = create_taxonomy(**serializer.validated_data)
