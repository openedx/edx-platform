from rest_framework import viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from third_party_auth.models import SAMLProviderConfig
from third_party_auth.samlproviderconfig.serializers import SAMLProviderConfigSerializer

class SAMLProviderConfigViewSet(viewsets.ViewSet):
    """
    A ViewSet to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/samlproviderconfig/
    """

    def retrieve(self, request, pk=None):
        """
            GET /auth/samlproviderconfig/{samlproviderconfigId}
        """
        queryset = SAMLProviderConfig.objects.all()
        samlprovider_config = get_object_or_404(queryset, pk=pk)
        serializer = SAMLProviderConfigSerializer(samlprovider_config)
        return Response(serializer.data)
    
    def list(self, request):
        pass

    def create(self, request):
        pass

    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass
