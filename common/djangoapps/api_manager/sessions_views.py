# pylint: disable=E1101

""" API specification for Session-oriented interactions """

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, load_backend
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ObjectDoesNotExist
from django.utils.importlib import import_module

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from api_manager.permissions import ApiKeyHeaderPermission
from api_manager.serializers import UserSerializer


@api_view(['POST'])
@permission_classes((ApiKeyHeaderPermission,))
def session_list(request):
    """
    POST creates a new system session, supported authentication modes:
    1. Open edX username/password
    """
    if request.method == 'POST':
        response_data = {}
        try:
            existing_user = User.objects.get(username=request.DATA['username'])
        except ObjectDoesNotExist:
            existing_user = None
        if existing_user:
            user = authenticate(username=existing_user.username, password=request.DATA['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    response_data['token'] = request.session.session_key
                    response_data['expires'] = request.session.get_expiry_age()
                    user_dto = UserSerializer(user)
                    response_data['user'] = user_dto.data
                    response_data['uri'] = '{}/{}'.format(request.path, request.session.session_key)
                    response_status = status.HTTP_201_CREATED
                else:
                    response_status = status.HTTP_403_FORBIDDEN
            else:
                response_status = status.HTTP_401_UNAUTHORIZED
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def session_detail(request, session_id):
    """
    GET retrieves an existing system session
    DELETE flushes an existing system session from the system
    """
    response_data = {}
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore(session_id)
    if request.method == 'GET':
        try:
            user_id = session[SESSION_KEY]
            backend_path = session[BACKEND_SESSION_KEY]
            backend = load_backend(backend_path)
            user = backend.get_user(user_id) or AnonymousUser()
        except KeyError:
            user = AnonymousUser()
        if user.is_authenticated():
            response_data['token'] = session.session_key
            response_data['expires'] = session.get_expiry_age()
            response_data['uri'] = request.path
            response_data['user_id'] = user.id
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    elif request.method == 'DELETE':
        session.flush()
        return Response(response_data, status=status.HTTP_204_NO_CONTENT)
