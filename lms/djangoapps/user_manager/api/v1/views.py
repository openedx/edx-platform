from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.response import Response

from openedx.core.lib.api.view_utils import view_auth_classes
from .serializers import ManagerListSerializer, ManagerReportsSerializer, UserManagerSerializer
from ...models import UserManagerRole


@view_auth_classes(is_authenticated=True)
class ManagerListView(ListAPIView):
    """
    See a list of all managers. Lists their id (if any) and email.
    """
    serializer_class = ManagerListSerializer
    queryset = UserManagerRole.objects.values(
        'manager_user',
        'manager_user__email',
        'unregistered_manager_email',
    ).distinct()


@view_auth_classes(is_authenticated=True)
class ManagerReportsListView(ListCreateAPIView):
    """
    See a list of all direct reports for a manager. Lists their id and email.
    """
    serializer_class = ManagerReportsSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        if '@' in username:
            return UserManagerRole.objects.filter(
                Q(manager_user__email=username) |
                Q(unregistered_manager_email=username),
            )
        else:
            return UserManagerRole.objects.filter(
                manager_user__username=username,
            )

    def perform_create(self, serializer):
        manager_id = self.kwargs['username']
        email = serializer.validated_data.get('user', {}).get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotFound(detail='No user with that email')

        if '@' in manager_id:
            try:
                manager_user = User.objects.get(email=manager_id)
            except User.DoesNotExist:
                serializer.save(user=user, unregistered_manager_email=manager_id)
                return
        else:
            manager_user = User.objects.get(username=manager_id)

        serializer.save(manager_user=manager_user, user=user)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@view_auth_classes(is_authenticated=True)
class UserManagerListView(ListCreateAPIView):
    """
    See a list of all managers for a particular user. Lists their id (if any) and email.
    """
    serializer_class = UserManagerSerializer

    @staticmethod
    def _get_user_by_username_or_email(userid):
        if '@' in userid:
            return User.objects.get(email=userid)
        else:
            return User.objects.get(username=userid)

    def get_queryset(self):
        username = self.kwargs['username']
        if '@' in username:
            return UserManagerRole.objects.filter(user__email=username)
        else:
            return UserManagerRole.objects.filter(user__username=username)

    def perform_create(self, serializer):
        try:
            user = self._get_user_by_username_or_email(self.kwargs['username'])
        except User.DoesNotExist:
            raise NotFound(detail='No user with that email')

        manager_email = serializer.validated_data.get('manager_email')

        try:
            manager = User.objects.get(email=manager_email)
            serializer.save(manager_user=manager, user=user)
        except User.DoesNotExist:
            serializer.save(unregistered_manager_email=manager_email, user=user)

    def delete(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
