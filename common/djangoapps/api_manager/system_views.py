""" BASE API VIEWS """

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_manager.permissions import ApiKeyHeaderPermission


@api_view(['GET'])
@permission_classes((ApiKeyHeaderPermission,))
def system_detail(request):
    """Returns top-level descriptive information about the Open edX API"""
    response_data = {}
    response_data['name'] = "Open edX System API"
    response_data['description'] = "System interface for managing groups, users, and sessions."
    response_data['documentation'] = "http://docs.openedxapi.apiary.io/#get-%2Fapi%2Fsystem"
    response_data['uri'] = request.path
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((ApiKeyHeaderPermission,))
def api_detail(request):
    """Returns top-level descriptive information about the Open edX API"""
    response_data = {}
    response_data['name'] = "Open edX API"
    response_data['description'] = "Machine interface for interactions with Open edX."
    response_data['documentation'] = "http://docs.openedxapi.apiary.io"
    response_data['uri'] = request.path
    response_data['resources'] = []
    response_data['resources'].append({'uri': '/api/groups'})
    response_data['resources'].append({'uri': '/api/sessions'})
    response_data['resources'].append({'uri': '/api/system'})
    response_data['resources'].append({'uri': '/api/users'})
    return Response(response_data, status=status.HTTP_200_OK)
