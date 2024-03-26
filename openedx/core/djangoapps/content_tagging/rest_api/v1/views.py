"""
Tagging Org API Views
"""
from __future__ import annotations

import csv
from typing import Iterator

from django.db.models import Count
from django.http import StreamingHttpResponse
from opaque_keys.edx.keys import UsageKey
from openedx_tagging.core.tagging import rules as oel_tagging_rules
from openedx_tagging.core.tagging.rest_api.v1.views import ObjectTagView, TaxonomyView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ...api import (
    create_taxonomy,
    get_all_object_tags,
    get_taxonomies,
    get_taxonomies_for_org,
    get_taxonomy,
    get_unassigned_taxonomies,
    set_taxonomy_orgs
)
from ...rules import get_admin_orgs
from ...utils import get_content_key_from_string
from .filters import ObjectTagTaxonomyOrgFilterBackend, UserOrgFilterBackend
from .objecttag_export_helpers import build_object_tree_with_objecttags, iterate_with_level
from .serializers import TaxonomyOrgListQueryParamsSerializer, TaxonomyOrgSerializer, TaxonomyUpdateOrgBodySerializer


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

        # If org filtering was requested, then use it, even if the org is invalid/None
        if "org" in query_params.validated_data:
            queryset = get_taxonomies_for_org(enabled, org)
        elif "unassigned" in query_params.validated_data:
            queryset = get_unassigned_taxonomies(enabled)
        else:
            queryset = get_taxonomies(enabled)

        # Prefetch taxonomyorgs so we can check permissions
        queryset = queryset.prefetch_related("taxonomyorg_set__org")

        # Annotate with tags_count to avoid selecting all the tags
        queryset = queryset.annotate(tags_count=Count("tag", distinct=True))

        return queryset

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
    This view extends the ObjectTagView to add Organization filters for the results.

    Refer to ObjectTagView docstring for usage details.
    """
    filter_backends = [ObjectTagTaxonomyOrgFilterBackend]


class ObjectTagExportView(APIView):
    """"
    View to export a CSV with all children and tags for a given course/context.
    """
    def get(self, request: Request, **kwargs) -> StreamingHttpResponse:
        """
        Export a CSV with all children and tags for a given course/context.
        """

        class Echo(object):
            """
            Class that implements just the write method of the file-like interface,
            used for the streaming response.
            """
            def write(self, value):
                return value

        def _generate_csv_rows() -> Iterator[str]:
            """
            Receives the blocks, tags and taxonomies and returns a CSV string
            """

            header = {"name": "Name", "type": "Type", "id": "ID"}

            # Prepare the header for the taxonomies
            for taxonomy_id, taxonomy in taxonomies.items():
                header[f"taxonomy_{taxonomy_id}"] = taxonomy.export_id

            csv_writer = csv.DictWriter(pseudo_buffer, fieldnames=header.keys(), quoting=csv.QUOTE_NONNUMERIC)
            yield csv_writer.writerow(header)

            # Iterate over the blocks and yield the rows
            for item, level in iterate_with_level(tagged_content):
                block_data = {
                    "name": level * "  " + item.display_name,
                    "type": item.category,
                    "id": item.block_id,
                }

                # Add the tags for each taxonomy
                for taxonomy_id in taxonomies:
                    if taxonomy_id in item.object_tags:
                        tag_values = item.object_tags[taxonomy_id]
                        block_data[f"taxonomy_{taxonomy_id}"] = ", ".join(tag_values)

                yield csv_writer.writerow(block_data)

        object_id: str = kwargs.get('context_id', None)

        try:
            content_key = get_content_key_from_string(object_id)

            if isinstance(content_key, UsageKey):
                raise ValidationError("The object_id must be a CourseKey or a LibraryLocatorV2.")

            # Check if the user has permission to view object tags for this object_id
            if not self.request.user.has_perm(
                "oel_tagging.view_objecttag",
                # The obj arg expects a model, but we are passing an object
                oel_tagging_rules.ObjectTagPermissionItem(taxonomy=None, object_id=object_id),  # type: ignore[arg-type]
            ):
                raise PermissionDenied(
                    "You do not have permission to view object tags for this object_id."
                )

            all_object_tags, taxonomies = get_all_object_tags(content_key)
            tagged_content = build_object_tree_with_objecttags(content_key, all_object_tags)

        except ValueError as e:
            raise ValidationError from e

        pseudo_buffer = Echo()

        return StreamingHttpResponse(
            streaming_content=_generate_csv_rows(),
            content_type="text/csv",
            headers={'Content-Disposition': f'attachment; filename="{object_id}_tags.csv"'},
        )
