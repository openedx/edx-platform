from django.contrib.auth import get_user_model
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response

from experiments import filters, serializers
from experiments.models import ExperimentData, ExperimentKeyValue
from experiments.permissions import IsStaffOrOwner, IsStaffOrReadOnly
from openedx.core.lib.api.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf

User = get_user_model()  # pylint: disable=invalid-name


class ExperimentCrossDomainSessionAuth(SessionAuthenticationAllowInactiveUser, SessionAuthenticationCrossDomainCsrf):
    """Session authentication that allows inactive users and cross-domain requests. """
    pass


class ExperimentDataViewSet(viewsets.ModelViewSet):
    authentication_classes = (JwtAuthentication, ExperimentCrossDomainSessionAuth,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = filters.ExperimentDataFilter
    permission_classes = (permissions.IsAuthenticated, IsStaffOrOwner,)
    queryset = ExperimentData.objects.all()
    serializer_class = serializers.ExperimentDataSerializer
    _cached_users = {}

    def filter_queryset(self, queryset):
        queryset = queryset.filter(user=self.request.user)
        return super(ExperimentDataViewSet, self).filter_queryset(queryset)

    def get_serializer_class(self):
        if self.action == 'create':
            return serializers.ExperimentDataCreateSerializer
        return serializers.ExperimentDataSerializer

    def create_or_update(self, request, *args, **kwargs):
        # If we have a primary key, treat this as a regular update request
        if self.kwargs.get('pk'):
            return self.update(request, *args, **kwargs)

        # If we only have data, check to see if an instance exists in the database. If so, update it.
        # Otherwise, create a new instance.
        experiment_id = request.data.get('experiment_id')
        key = request.data.get('key')

        if experiment_id and key:
            try:
                obj = self.get_queryset().get(user=self.request.user, experiment_id=experiment_id, key=key)
                self.kwargs['pk'] = obj.pk
                return self.update(request, *args, **kwargs)
            except ExperimentData.DoesNotExist:
                pass

        self.action = 'create'
        return self.create(request, *args, **kwargs)

    def _cache_users(self, usernames):
        users = User.objects.filter(username__in=usernames)
        self._cached_users = {user.username: user for user in users}

    def _get_user(self, username):
        user = self._cached_users.get(username)

        if not user:
            user = User.objects.get(username=username)
            self._cached_users[username] = user

        return user

    @list_route(methods=['put'], permission_classes=[permissions.IsAdminUser])
    def bulk_upsert(self, request):
        upserted = []
        self._cache_users([datum['user'] for datum in request.data])

        with transaction.atomic():
            for item in request.data:
                user = self._get_user(username=item['user'])
                datum, __ = ExperimentData.objects.update_or_create(
                    user=user, experiment_id=item['experiment_id'], key=item['key'], defaults={'value': item['value']})
                upserted.append(datum)

            serializer = self.get_serializer(upserted, many=True)
            return Response(serializer.data)


class ExperimentKeyValueViewSet(viewsets.ModelViewSet):
    authentication_classes = (JwtAuthentication, ExperimentCrossDomainSessionAuth,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = filters.ExperimentKeyValueFilter
    permission_classes = (IsStaffOrReadOnly,)
    queryset = ExperimentKeyValue.objects.all()
    serializer_class = serializers.ExperimentKeyValueSerializer

    @list_route(methods=['put'], permission_classes=[permissions.IsAdminUser])
    def bulk_upsert(self, request):
        upserted = []

        with transaction.atomic():
            for item in request.data:
                datum, __ = ExperimentKeyValue.objects.update_or_create(
                    experiment_id=item['experiment_id'], key=item['key'], defaults={'value': item['value']})
                upserted.append(datum)

            serializer = self.get_serializer(upserted, many=True)
            return Response(serializer.data)
