""" API specification for User-oriented interactions """

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_manager.permissions import ApiKeyHeaderPermission


def _serialize_user(response_data, user):
    """
    Loads the object data into the response dict
    This should probably evolve to use DRF serializers
    """
    response_data['email'] = user.email
    response_data['username'] = user.username
    response_data['first_name'] = user.first_name
    response_data['last_name'] = user.last_name
    response_data['id'] = user.id
    return response_data


@api_view(['POST'])
@permission_classes((ApiKeyHeaderPermission,))
def user_list(request):
    """
    POST creates a new user in the system
    """
    if request.method == 'POST':
        response_data = {}
        email = request.DATA['email']
        username = request.DATA['username']
        password = request.DATA['password']
        first_name = request.DATA.get('first_name', '')
        last_name = request.DATA.get('last_name', '')
        try:
            user = User.objects.create(email=email, username=username)
        except IntegrityError:
            user = None
        else:
            user.set_password(password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        if user:
            status_code = status.HTTP_201_CREATED
            response_data = _serialize_user(response_data, user)
            response_data['uri'] = request.path + '/' + str(user.id)
        else:
            status_code = status.HTTP_409_CONFLICT
            response_data['message'] = "User '%s' already exists", username
            response_data['field_conflict'] = "username"
        return Response(response_data, status=status_code)


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def user_detail(request, user_id):
    """
    GET retrieves an existing user from the system
    DELETE removes/inactivates/etc. an existing user
    """
    if request.method == 'GET':
        response_data = {}
        try:
            existing_user = User.objects.get(id=user_id, is_active=True)
            _serialize_user(response_data, existing_user)
            response_data['uri'] = request.path
            response_data['resources'] = []
            resource_uri = '/api/users/%s/groups' % user_id
            response_data['resources'].append({'uri': resource_uri})
            return Response(response_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'DELETE':
        response_data = {}
        try:
            existing_user = User.objects.get(id=user_id, is_active=True)
            existing_user.is_active = False
            existing_user.save()
        except ObjectDoesNotExist:
            # It's ok if we don't find a match
            pass
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((ApiKeyHeaderPermission,))
def user_groups_list(request, user_id):
    """
    POST creates a new user-group relationship in the system
    """
    if request.method == 'POST':
        response_data = {}
        user_id = user_id
        group_id = request.DATA['group_id']
        try:
            existing_user = User.objects.get(id=user_id)
            existing_user.groups.add(group_id)
            response_data['uri'] = request.path + '/' + str(group_id)
            response_data['user_id'] = str(user_id)
            response_data['group_id'] = str(group_id)
            return Response(response_data, status=status.HTTP_201_CREATED)
        except IntegrityError:
            response_data['uri'] = request.path + '/' + str(group_id)
            response_data['message'] = "Relationship already exists."
            return Response(response_data, status=status.HTTP_409_CONFLICT)


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def user_groups_detail(request, user_id, group_id):
    """
    GET retrieves an existing user-group relationship from the system
    DELETE removes/inactivates/etc. an existing user-group relationship
    """
    if request.method == 'GET':
        response_data = {}
        try:
            existing_user = User.objects.get(id=user_id, is_active=True)
            existing_relationship = existing_user.groups.get(id=group_id)
        except ObjectDoesNotExist:
            existing_user = None
            existing_relationship = None
        if existing_user and existing_relationship:
            response_data['user_id'] = existing_user.id
            response_data['group_id'] = existing_relationship.id
            response_data['uri'] = request.path
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)
    elif request.method == 'DELETE':
        existing_user = User.objects.get(id=user_id, is_active=True)
        existing_user.groups.remove(group_id)
        existing_user.save()
        return Response({}, status=status.HTTP_204_NO_CONTENT)
