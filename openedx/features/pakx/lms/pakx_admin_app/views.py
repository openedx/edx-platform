from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django.db.models import F
from rest_framework import viewsets, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from .constants import GROUP_TRAINING_MANAGERS, ADMIN, STAFF, TRAINING_MANAGER, LEARNER
from .permissions import CanAccessPakXAdminPanel
from .pagination import PakxAdminAppPagination
from .serializers import UserSerializer


class UserProfileViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [CanAccessPakXAdminPanel]
    pagination_class = PakxAdminAppPagination
    serializer_class = UserSerializer
    filter_backends = [OrderingFilter]
    OrderingFilter.ordering_fields = ('id', 'name', 'email', 'employee_id')
    ordering = ['-id']

    def destroy(self, request, *args, **kwargs):
        if self.get_queryset().filter(id=kwargs['pk']).update(is_active=False):
            return Response(status=status.HTTP_200_OK)

        return Response({"ID not found": kwargs['pk']}, status=status.HTTP_404_NOT_FOUND)

    def list(self, request, *args, **kwargs):
        roles = self.request.query_params['roles'].split(',') if self.request.query_params.get('roles') else []
        roles_qs = self.get_roles_q_filters(roles)

        self.queryset = self.get_queryset()

        if roles_qs:
            self.queryset = self.queryset.filter(roles_qs)

        languages = self.request.query_params['languages'].split(',') if self.request.query_params.get(
            'languages') else []

        if languages:
            self.queryset = self.queryset.filter(profile__language__in=languages)

        page = self.paginate_queryset(self.queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)

        return Response(self.get_serializer(self.queryset, many=True).data)

    def get_queryset(self):
        if self.request.query_params.get("ordering"):
            self.ordering = self.request.query_params['ordering'].split(',') + self.ordering

        if self.request.user.is_superuser:
            queryset = User.objects.all()
        else:
            queryset = User.objects.filter(
                attributes__name="org",
                attributes__value=self.request.user.attributes.filter(name="org").first().value
            )

        return queryset.annotate(employee_id=F('profile__employee_id'), name=F('first_name')).order_by(*self.ordering)

    def activate_users(self, request, *args, **kwargs):
        return self.change_activation_status(True, request.data["ids"])

    def deactivate_users(self, request, *args, **kwargs):
        return self.change_activation_status(False, request.data["ids"])

    def get_roles_q_filters(self, roles):
        qs = Q()

        for role in roles:
            if int(role) == ADMIN:
                qs |= Q(is_superuser=True)
            elif int(role) == STAFF:
                qs |= Q(is_staff=True)
            elif int(role) == LEARNER:
                qs |= ~Q(Q(is_superuser=True) | Q(is_staff=True) | Q(groups__name=GROUP_TRAINING_MANAGERS))
            elif int(role) == TRAINING_MANAGER:
                qs |= Q(groups__name=GROUP_TRAINING_MANAGERS)

        return qs

    def change_activation_status(self, activation_status, ids):
        if ids == "all":
            self.get_queryset().all().update(is_active=activation_status)
            return Response(status=status.HTTP_200_OK)

        if self.get_queryset().filter(id__in=ids).update(is_active=activation_status):
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)
