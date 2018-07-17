from django.db.models import Q
from rest_framework.generics import ListAPIView, ListCreateAPIView

from openedx.core.lib.api.view_utils import view_auth_classes
from .serializers import UserManagerSerializer, UserManagerReportsSerializer
from ...models import UserManagerRole


@view_auth_classes(is_authenticated=True)
class ManagerListView(ListAPIView):
    """
    See a list of all managers. Lists their id (if any) and email.


    """
    serializer_class = UserManagerSerializer
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
    serializer_class = UserManagerReportsSerializer

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


@view_auth_classes(is_authenticated=True)
class UserManagerListView(ListAPIView):
    """
    See a list of all managers for a particular user. Lists their id (if any) and email.


    """
    serializer_class = UserManagerSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        if '@' in username:
            queryset = UserManagerRole.objects.filter(user__email=username)
        else:
            queryset = UserManagerRole.objects.filter(user__username=username)
        return queryset.values(
            'manager_user',
            'manager_user__email',
            'unregistered_manager_email',
        )
