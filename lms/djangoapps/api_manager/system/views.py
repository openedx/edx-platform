""" BASE API VIEWS """
from django.middleware.csrf import get_token

from rest_framework import status
from rest_framework.response import Response

from api_manager.permissions import SecureAPIView
from api_manager.utils import generate_base_uri


class SystemDetail(SecureAPIView):
    """Manages system-level information about the Open edX API"""

    def get(self, request):
        base_uri = generate_base_uri(request)
        response_data = {}
        response_data['name'] = "Open edX System API"
        response_data['description'] = "System interface for managing groups, users, and sessions."
        response_data['documentation'] = "http://docs.openedxapi.apiary.io/#get-%2Fapi%2Fsystem"
        response_data['uri'] = base_uri
        return Response(response_data, status=status.HTTP_200_OK)


class ApiDetail(SecureAPIView):
    """Manages top-level information about the Open edX API"""

    def get(self, request):
        base_uri = generate_base_uri(request)
        response_data = {}
        response_data['name'] = "Open edX API"
        response_data['description'] = "Machine interface for interactions with Open edX."
        response_data['documentation'] = "http://docs.openedxapi.apiary.io"
        response_data['uri'] = base_uri
        response_data['csrf_token'] = get_token(request)
        response_data['resources'] = []
        response_data['resources'].append({'uri': base_uri + 'courses'})
        response_data['resources'].append({'uri': base_uri + 'groups'})
        response_data['resources'].append({'uri': base_uri + 'projects'})
        response_data['resources'].append({'uri': base_uri + 'sessions'})
        response_data['resources'].append({'uri': base_uri + 'system'})
        response_data['resources'].append({'uri': base_uri + 'users'})
        return Response(response_data, status=status.HTTP_200_OK)
