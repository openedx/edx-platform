"""
APIs for the Platform 2.0.
"""

import logging

from rest_framework import views, status
from rest_framework.response import Response

import tahoe_sites.api

from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


log = logging.Logger(__name__)


class CompileSassView(views.APIView):
    """
    Compiles Tahoe Site Sass via API by:
        - initializing the `api_adapter` for the site
        - calling SiteConfiguration.compile_microsite_sass()

    Usage:

        POST /appsembler/api/compile_sass/
            {"site_uuid": "fake-site-uuid"}
    """
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, format=None):
        site_uuid = request.data['site_uuid']
        site = tahoe_sites.api.get_site_by_uuid(site_uuid)
        configuration = SiteConfiguration.objects.get(site=site)
        configuration.init_api_client_adapter(site)
        configuration.compile_microsite_sass()
        return Response(status=status.HTTP_200_OK)
