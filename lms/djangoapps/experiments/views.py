from edx_rest_framework_extensions.authentication import JwtAuthentication
from rest_framework import permissions, viewsets
from rest_framework.filters import DjangoFilterBackend

from experiments import filters
from experiments.models import ExperimentData
from experiments.permissions import IsStaffOrOwner
from experiments.serializers import ExperimentDataCreateSerializer, ExperimentDataSerializer
from openedx.core.lib.api.authentication import SessionAuthenticationAllowInactiveUser


class ExperimentDataViewSet(viewsets.ModelViewSet):
    authentication_classes = (JwtAuthentication, SessionAuthenticationAllowInactiveUser,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = filters.ExperimentDataFilter
    permission_classes = (permissions.IsAuthenticated, IsStaffOrOwner,)
    queryset = ExperimentData.objects.all()
    serializer_class = ExperimentDataSerializer

    def filter_queryset(self, queryset):
        queryset = queryset.filter(user=self.request.user)
        return super(ExperimentDataViewSet, self).filter_queryset(queryset)

    def get_serializer_class(self):
        if self.action == 'create':
            return ExperimentDataCreateSerializer
        return ExperimentDataSerializer

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
                self.request.data['id'] = obj.pk
                return self.update(request, *args, **kwargs)
            except ExperimentData.DoesNotExist:
                pass

        self.action = 'create'
        return self.create(request, *args, **kwargs)
