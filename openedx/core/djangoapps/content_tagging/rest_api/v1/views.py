"""
Tagging Org API Views
"""
from django.db.models.query import QuerySet
from django.http import HttpResponse
from openedx_tagging.core.tagging import rules as oel_tagging_rules
from openedx_tagging.core.tagging.models import ObjectTag
from openedx_tagging.core.tagging.rest_api.v1.views import ObjectTagView, TaxonomyView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from ...api import (
    create_taxonomy,
    export_content_object_children_tags,
    get_taxonomy,
    get_taxonomies,
    get_taxonomies_for_org,
    get_unassigned_taxonomies,
    set_taxonomy_orgs,
)
from ...rules import get_admin_orgs
from .serializers import (
    ContentObjectChildrenTagsExportQueryParamsSerializer,
    TaxonomyOrgListQueryParamsSerializer,
    TaxonomyOrgSerializer,
    TaxonomyUpdateOrgBodySerializer,
)
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
        unassigned = query_params.validated_data.get("unassigned", None)
        org = query_params.validated_data.get("org", None)

        # Raise an error if both "org" and "unassigned" query params were provided
        if "org" in query_params.validated_data and "unassigned" in query_params.validated_data:
            raise ValidationError("'org' and 'unassigned' params cannot be both defined")

        # If org filtering was requested, then use it, even if the org is invalid/None
        if "org" in query_params.validated_data:
            queryset = get_taxonomies_for_org(enabled, org)
        elif "unassigned" in query_params.validated_data:
            queryset = get_unassigned_taxonomies(enabled)
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
    def create_import(self, request: Request, **kwargs) -> Response:  # type: ignore
        """
        Creates a new taxonomy with the given orgs and imports the tags from the uploaded file.
        """
        response = super().create_import(request=request, **kwargs)  # type: ignore

        # If creation was successful, set the orgs for the new taxonomy
        if status.is_success(response.status_code):
            # ToDo: This code is temporary
            # In the future, the orgs parameter will be defined in the request body from the frontend
            # See: https://github.com/openedx/modular-learning/issues/116
            if oel_tagging_rules.is_taxonomy_admin(request.user):
                orgs = None
            else:
                orgs = get_admin_orgs(request.user)

            taxonomy = get_taxonomy(response.data["id"])
            assert taxonomy
            set_taxonomy_orgs(taxonomy, all_orgs=False, orgs=orgs)

            serializer = self.get_serializer(taxonomy)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return response

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
    This view extends the ObjectTagView to add Organization filters for the results and
    new actions like: export.

    Refer to ObjectTagView docstring for usage details.
    """
    filter_backends = [ObjectTagTaxonomyOrgFilterBackend]

    def get_queryset(self):
        if self.action == "retrieve":
            return super().get_queryset()

        # For other actions, return a dummy queryset only for permission checking
        dummy_queryset = QuerySet(model=ObjectTag)

        return dummy_queryset

    @action(detail=True, url_path="export", methods=["get"])
    def export_children_object_tags(self, request: Request, **kwargs) -> HttpResponse:
        """
        Export all the object tags for the given object_id children.
        """
        object_id: str = kwargs.get('object_id', None)

        query_params = ContentObjectChildrenTagsExportQueryParamsSerializer(
            data=request.query_params.dict()
        )
        query_params.is_valid(raise_exception=True)

        # Check if the user has permission to view object tags for this object_id
        try:
            if not self.request.user.has_perm(
                "oel_tagging.view_objecttag",
                # The obj arg expects a model, but we are passing an object
                oel_tagging_rules.ObjectTagPermissionItem(taxonomy=None, object_id=object_id),  # type: ignore[arg-type]
            ):
                raise PermissionDenied(
                    "You do not have permission to view object tags for this object_id."
                )
        except ValueError as e:
            raise ValidationError from e

        if query_params.data.get("download"):
            content_type = "text/csv"
        else:
            content_type = "text"

        tags = export_content_object_children_tags(object_id)

        if query_params.data.get("download"):
            response = HttpResponse(tags.encode('utf-8'), content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{object_id}_tags.csv"'
            return response

        return HttpResponse(tags, content_type=content_type)
