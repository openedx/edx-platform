"""
Credentials service API views (v1).
"""
from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service.models import UserCredential
from rest_framework import mixins, viewsets


class UserCredentialViewSet(mixins.CreateModelMixin,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    """
    """
    queryset = UserCredential.objects.all()
    serializer_class = serializers.UserCredentialSerializer
