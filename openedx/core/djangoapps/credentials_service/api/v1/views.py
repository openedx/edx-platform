"""
Credentials service API views (v1).
"""
from django.contrib.contenttypes.models import ContentType
from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service import filters
from openedx.core.djangoapps.credentials_service.models import UserCredential, ProgramCertificate, CourseCertificate, \
    UserCredentialAttribute
from openedx.core.lib.api import parsers
from rest_framework import mixins, viewsets, parsers as drf_parsers

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status


class UserCredentialViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    queryset = UserCredential.objects.all()
    lookup_field = 'username'
    serializer_class = serializers.UserCredentialSerializer
    parser_classes = (parsers.MergePatchParser,  drf_parsers.JSONParser)

    def create(self, request, *args, **kwargs):
        """ Creates refunds, if eligible orders exist. """
        username = request.data.get('username')
        download_url = request.data.get('download_url')

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/user/v1/preferences/{username}/
        """
        UserCredential.objects.filter(pk = request.data.get('id')).update(
            status = request.data.get('status')
        )
        return Response('done', status=status.HTTP_200_OK)

    def update(request, *args, **kwargs):
        """
        PATCH /api/user/v1/preferences/{username}/
        """
        pass


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

    def create(self, request, *args, **kwargs):
        program_id = request.data.get('program_id')
        username = request.data.get('username')
        attributes = request.data.get('attributes')
        try:
            program = ProgramCertificate.objects.get(program_id=program_id)
        except ProgramCertificate.DoesNotExist():
            return

        new_credenential = UserCredential(username=username, credential=program)
        new_credenential.save()

        attrs_list =[]
        for attr in attributes:
            attrs_list.append(
                UserCredentialAttribute(
                    user_credential=new_credenential,
                    namespace=attr.get('namespace'),
                    name=attr.get('name'),
                    value=attr.get('value')
                )
            )

        UserCredentialAttribute.objects.bulk_create(attrs_list)

        return Response('done', status=status.HTTP_200_OK)

class CredentialsByCoursesViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    # TODO docstrings.

    lookup_field = 'course_id'
    queryset = CourseCertificate.objects.all()
    serializer_class = serializers.CourseCertificateSerializer

    parser_classes = (parsers.MergePatchParser,)


