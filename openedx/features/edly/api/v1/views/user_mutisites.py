"""
Views for user sites API
"""
import urllib.parse 

from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication

from openedx.features.edly.api.serializers import MutiSiteAccessSerializer
from openedx.core.lib.api.authentication import BearerAuthentication
from openedx.features.edly.models import EdlyMultiSiteAccess
from openedx.features.edly.utils import get_edly_sub_org_from_request


class MultisitesViewset(viewsets.ViewSet):
    """
    **Use Case**

        Get information about the current user's linked sites using email.

    **Example Request**

        GET /api/v1/user_link_sites/?email=<edx%40example.com>

    **Response Values**

        If the request is successful, the request returns an HTTP 200 "OK" response.

        The HTTP 200 response has the following values.

        * list of sub-organization linked with your email

    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [BearerAuthentication, SessionAuthentication]


    def list(self, request, *args, **kwargs):
        """
        Returns a list of Site linked with the user email 
        """
        email = request.GET.get('email', '')
        if email:
            queryset = EdlyMultiSiteAccess.objects.filter(user__email=urllib.parse.unquote(email))
        else:
            sub_org = get_edly_sub_org_from_request(request)
            queryset = EdlyMultiSiteAccess.objects.filter(
                user=request.user, 
                sub_org__edly_organization=sub_org.edly_organization
            )

        serializer = MutiSiteAccessSerializer(queryset, many=True)
        return Response(serializer.data)
