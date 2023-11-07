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

