"""
Credentials service API views (v1).
"""
from django.contrib.contenttypes.models import ContentType
from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service import filters
from openedx.core.djangoapps.credentials_service.models import UserCredential, ProgramCertificate
from openedx.core.lib.api import parsers
from rest_framework import mixins, viewsets

from rest_framework import generics

class UserCredentialViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    lookup_field = 'username'
    queryset = UserCredential.objects.all()
    serializer_class = serializers.UserCredentialSerializer
    parser_classes = (parsers.MergePatchParser,)


class CredentialsByProgramsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    # TODO docstrings.

    lookup_field = 'program_id'
    queryset = ProgramCertificate.objects.all()
    serializer_class = serializers.ProgramCertificateSerializer
    # filter_backends = (
    #     filters.ProgramSearchFilterBackend,
    # )

    parser_classes = (parsers.MergePatchParser,)


