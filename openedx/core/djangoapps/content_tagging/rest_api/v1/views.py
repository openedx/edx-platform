"""
Tagging Org API Views
"""
from openedx_tagging.core.tagging import rules as oel_tagging_rules
from openedx_tagging.core.tagging.import_export.api import get_last_import_log, import_tags
from openedx_tagging.core.tagging.rest_api.v1.serializers import TaxonomyImportBodySerializer, TaxonomyImportNewBodySerializer
from openedx_tagging.core.tagging.rest_api.v1.views import ObjectTagView, TaxonomyView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response

from ...api import (
    create_taxonomy,
    get_taxonomies,
    get_taxonomies_for_org,
    set_taxonomy_orgs,
)
from ...rules import get_admin_orgs
from .serializers import TaxonomyOrgListQueryParamsSerializer, TaxonomyOrgSerializer, TaxonomyUpdateOrgBodySerializer
from .filters import ObjectTagTaxonomyOrgFilterBackend, UserOrgFilterBackend


class TaxonomyOrgView(TaxonomyView):
    """
    View to list, create, retrieve, update, delete, export or import Taxonomies.
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
    serializer_class = TaxonomyOrgSerializer

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
            queryset = get_taxonomies_for_org(enabled, org)
        else:
            queryset = get_taxonomies(enabled)

        return queryset.prefetch_related("taxonomyorg_set")

    def perform_create(self, serializer):
        """
        Create a new taxonomy.
        """
        user_admin_orgs = get_admin_orgs(self.request.user)
        serializer.instance = create_taxonomy(**serializer.validated_data, orgs=user_admin_orgs)

    @action(detail=False, url_path="import", methods=["post"])
    def create_import(self, request: Request, **_kwargs) -> Response:
        """
        Creates a new taxonomy and imports the tags from the uploaded file.
        """
        body = TaxonomyImportNewBodySerializer(data=request.data)
        body.is_valid(raise_exception=True)

        taxonomy_name = body.validated_data["taxonomy_name"]
        taxonomy_description = body.validated_data["taxonomy_description"]
        file = body.validated_data["file"].file
        parser_format = body.validated_data["parser_format"]

        # ToDo: This code is temporary
        # In the future, the orgs parameter will be defined in the request body from the frontend
        # See: https://github.com/openedx/modular-learning/issues/116
        if oel_tagging_rules.is_taxonomy_admin(request.user):
            orgs = None
        else:
            orgs = get_admin_orgs(request.user)

        taxonomy = create_taxonomy(taxonomy_name, taxonomy_description, orgs=orgs)
        try:
            import_success = import_tags(taxonomy, file, parser_format)

            if import_success:
                serializer = self.get_serializer(taxonomy)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                import_error = get_last_import_log(taxonomy)
                taxonomy.delete()
                return Response(import_error, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, url_path="tags/import", methods=["put"])
    def update_import(self, request: Request, **_kwargs) -> Response:
        """
        Creates a new taxonomy and imports the tags from the uploaded file.
        """
        body = TaxonomyImportBodySerializer(data=request.data)
        body.is_valid(raise_exception=True)

        file = body.validated_data["file"].file
        parser_format = body.validated_data["parser_format"]

        taxonomy = self.get_object()
        try:
            import_success = import_tags(taxonomy, file, parser_format)

            if import_success:
                serializer = self.get_serializer(taxonomy)
                return Response(serializer.data)
            else:
                import_error = get_last_import_log(taxonomy)
                return Response(import_error, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["put"])
    def orgs(self, request, **_kwargs) -> Response:
        """
        Update the orgs associated with taxonomies.
        """
        taxonomy = self.get_object()
        perm = "oel_tagging.update_orgs"
        if not request.user.has_perm(perm, taxonomy):
            raise PermissionDenied("You do not have permission to update the orgs associated with this taxonomy.")
        body = TaxonomyUpdateOrgBodySerializer(
            data=request.data,
        )
        body.is_valid(raise_exception=True)
        orgs = body.validated_data.get("orgs")
        all_orgs: bool = body.validated_data.get("all_orgs", False)

        set_taxonomy_orgs(taxonomy=taxonomy, all_orgs=all_orgs, orgs=orgs)

        return Response()


class ObjectTagOrgView(ObjectTagView):
    """
    View to create and retrieve ObjectTags for a provided Object ID (object_id).
    This view extends the ObjectTagView to add Organization filters for the results.

    Refer to ObjectTagView docstring for usage details.
    """
    filter_backends = [ObjectTagTaxonomyOrgFilterBackend]
