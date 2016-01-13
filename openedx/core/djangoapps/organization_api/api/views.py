"""
Organizations API views.
"""
from rest_framework import permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from rest_framework_oauth.authentication import OAuth2Authentication

from openedx.core.lib.api.authentication import JwtAuthentication
from util.organizations_helpers import get_organization_by_short_name


class OrganizationsView(APIView):
    """
    View to get organization information.
    """
    authentication_classes = (OAuth2Authentication, SessionAuthentication, JwtAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, organization_key):
        """
        Return organization information related to provided organization
        key/short_name.
        """
        organization = get_organization_by_short_name(organization_key)
        if organization:
            logo = organization.get('logo')
            organization_data = {
                'name': organization.get('name', ''),
                'short_name': organization.get('short_name', ''),
                'description': organization.get('description', ''),
                'logo': request.build_absolute_uri(logo.url) if logo else ''
            }

            return Response(organization_data)

        return Response(status=HTTP_404_NOT_FOUND)
