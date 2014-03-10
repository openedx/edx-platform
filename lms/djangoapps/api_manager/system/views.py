""" BASE API VIEWS """

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from api_manager.permissions import ApiKeyHeaderPermission


def _generate_base_uri(request):
    """
    Constructs the protocol:host:path component of the resource uri
    """
    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    resource_uri = '{}://{}{}'.format(
        protocol,
        request.get_host(),
        request.get_full_path()
    )
    return resource_uri

class SystemDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, format=None):
        """Returns top-level descriptive information about the Open edX API"""
        base_uri = _generate_base_uri(request)
        response_data = {}
        response_data['name'] = "Open edX System API"
        response_data['description'] = "System interface for managing groups, users, and sessions."
        response_data['documentation'] = "http://docs.openedxapi.apiary.io/#get-%2Fapi%2Fsystem"
        response_data['uri'] = base_uri
        return Response(response_data, status=status.HTTP_200_OK)


class ApiDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, format=None):
        """Returns top-level descriptive information about the Open edX API"""
        base_uri = _generate_base_uri(request)
        response_data = {}
        response_data['name'] = "Open edX API"
        response_data['description'] = "Machine interface for interactions with Open edX."
        response_data['documentation'] = "http://docs.openedxapi.apiary.io"
        response_data['uri'] = base_uri
        response_data['resources'] = []
        response_data['resources'].append({'uri': base_uri + 'courses'})
        response_data['resources'].append({'uri': base_uri + 'groups'})
        response_data['resources'].append({'uri': base_uri + 'sessions'})
        response_data['resources'].append({'uri': base_uri + 'system'})
        response_data['resources'].append({'uri': base_uri + 'users'})
        return Response(response_data, status=status.HTTP_200_OK)
