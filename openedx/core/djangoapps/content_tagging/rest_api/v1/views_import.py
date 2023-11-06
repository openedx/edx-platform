"""
Taxonomy import views
"""
from django.http import HttpResponse, HttpResponseBadRequest
from openedx_tagging.core.tagging import rules as oel_tagging_rules
from openedx_tagging.core.tagging.rest_api.v1.serializers import TaxonomyImportBodySerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.views import APIView

from ... import rules
from ...import_export import api as import_export_api


class ImportView(APIView):
    """
    View to import taxonomies

    **Example Requests**
        POST /content_tagging/rest_api/v1/import/
        {
            "taxonomy_name": "Taxonomy Name",
            "taxonomy_description": "This is a description",
            "file": <file>,
        }

    **Query Returns**
        * 200 - Success
        * 400 - Bad request
        * 405 - Method not allowed
    """
    http_method_names = ['post']

    def post(self, request: Request, *args, **kwargs) -> HttpResponse:
        """
        Imports the taxonomy from the uploaded file.
        """
        perm = "oel_tagging.import_taxonomy"
        if not request.user.has_perm(perm):
            raise PermissionDenied("You do not have permission to import taxonomies")

        body = TaxonomyImportBodySerializer(data=request.data)
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
            orgs = rules.get_admin_orgs(request.user)

        import_success = import_export_api.create_taxonomy_and_import_tags(
            taxonomy_name=taxonomy_name,
            taxonomy_description=taxonomy_description,
            file=file,
            parser_format=parser_format,
            orgs=orgs,
        )

        if import_success:
            return HttpResponse(status=200)
        else:
            return HttpResponseBadRequest("Error importing taxonomy")

