"""
    Viewset for auth/saml/v0/samlproviderconfig
"""

from rest_framework import viewsets
from rest_framework.decorators import action

from .models import SAMLProviderConfig
from .serializers import SAMLProviderConfigSerializer


class SAMLProviderMixin(object):
    queryset = SAMLProviderConfig.objects.all()
    serializer_class = SAMLProviderConfigSerializer
    # TODO: Authorization work pending, right now open API
    # permission_classes = [IsAdminUser]


class SAMLProviderConfigViewSet(SAMLProviderMixin, viewsets.ModelViewSet):
    """
    A View to handle SAMLProviderConfig CRUD

    Usage:
        [HttpVerb] /auth/saml/v0/providerconfig/
    """

    @action(methods=['put', detail=False])
    def update_existing(self, request, *args, **kwargs):
        provider_config = self.get_object()
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(provider_config, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
