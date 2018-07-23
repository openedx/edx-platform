from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.response import Response

from openedx.core.lib.api.view_utils import view_auth_classes
from .serializers import ManagerListSerializer, ManagerReportsSerializer, UserManagerSerializer
from ...models import UserManagerRole


def _filter_by_manager_id(queryset, manager_id):
    """
    Filters provided ``queryset`` by ``manager_id`` where ``manager_id``
    can be a username or email address.
    Args:
        queryset(QuerySet): UserManagerRole queryset
        manager_id(str): username or email address of manager
    Returns:
        queryset filtered by manager
    """
    if manager_id is None:
        return queryset
    elif '@' in manager_id:
        return queryset.filter(
            Q(manager_user__email=manager_id) |
            Q(unregistered_manager_email=manager_id),
        )
    else:
        return queryset.filter(
            manager_user__username=manager_id,
        )


def _filter_by_user_id(queryset, user_id):
    """
    Filters provided ``queryset`` by ``user_id`` where ``user_id`` can
    be a username or email address.
    Args:
        queryset(QuerySet): UserManagerRole queryset
        user_id(str): username or email address of user
    Returns:
        queryset filtered by user
    """
    if user_id is None:
        return queryset
    elif '@' in user_id:
        return queryset.filter(user__email=user_id)
    else:
        return queryset.filter(user__username=user_id)


@view_auth_classes(is_authenticated=True)
class ManagerListView(ListAPIView):
    """
        **Use Case**

            * Get a list of all users that are managers for other users

        **Example Request**

            GET /api/user_manager/v1/managers/

        **GET Parameters**

            None

        **GET Response Values**

            If the request for information about the managers is successful, an HTTP 200 "OK"
            response is returned with a collection of managers.

            The HTTP 200 response has the following values.

            * count: The number of managers in a course.

            * next: The URI to the next page of results.

            * previous: The URI to the previous page of results.

            * num_pages: The number of pages.

            * results: a list of manager users:

                * id: The user id for a manager user, or null if manager doesn't have an
                    account yet.

                * email: Email address of manager.

        **Example GET Response**

            {
                "count": 99,
                "next": "https://courses.org/api/user_manager/v1/managers/?page=2",
                "previous": null,
                "results": {
                    {
                        "email": "staff@example.com",
                        "id": 9
                    },
                    { ... }
                }
            }
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
        **Use Case**

            * Get a list of all users that are reports for the provided manager.

            * Add a user as a report under a manger.

            * Remove a user or all users under a manager.

        **Example Request**

            GET /api/user_manager/v1/reports/{user_id}/

            POST /api/user_manager/v1/reports/{user_id}/ {
                "email": "{email}"
            }

            DELETE /api/user_manager/v1/reports/{user_id}/

            DELETE /api/user_manager/v1/reports/{user_id}/?user={user_id}

        **GET Parameters**

            * user_id: username or email address for user whose reports you want fetch

        **POST Parameters**

            * user_id: username or email address for user for whom you want to add a manger

            * email: Email address for a user

        **DELETE Parameters**

            * user_id: username or email address for user

        **GET Response Values**

            If the request for information about the managers is successful, an HTTP 200 "OK"
            response is returned with a collection of managers.

            The HTTP 200 response has the following values.

            * count: The number of managers in a course.

            * next: The URI to the next page of results.

            * previous: The URI to the previous page of results.

            * num_pages: The number of pages.

            * results: a list of manager users:

                * id: The user id for a user.

                * email: Email address of user.

        **Example GET Response**

            GET /api/user_manager/v1/reports/edx@example.com/

            {
                "count": 99,
                "next": "https://courses.org/api/user_manager/v1/managers/?page=2",
                "previous": null,
                "results": {
                    {
                        "email": "staff@example.com",
                        "id": 9
                    },
                    { ... }
                }
            }

        **Example POST Response**

            POST /api/user_manager/v1/reports/edx@example.com/ {
                "email": "user@email.com"
            }

            {
                "email": "user@email.com"
                "id": 11
            }

        **Example DELETE Response**

            DELETE /api/user_manager/v1/reports/edx@exmaple.com/

            DELETE /api/user_manager/v1/reports/edx@exmaple.com/?report=some@user.com

    """
    serializer_class = ManagerReportsSerializer

    def get_queryset(self):
        username = self.kwargs['username']
        return _filter_by_manager_id(UserManagerRole.objects, username)

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

    def delete(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        user = request.query_params.get('user')
        queryset = _filter_by_user_id(self.get_queryset(), user)
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
        return _filter_by_user_id(UserManagerRole.objects, username)

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

    def delete(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        manager = request.query_params.get('manager')
        queryset = _filter_by_manager_id(self.get_queryset(), manager)
        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
