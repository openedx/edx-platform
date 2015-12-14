"""
Credentials service API views (v1).
"""
import logging
from openedx.core.djangoapps.credentials_service import serializers
from openedx.core.djangoapps.credentials_service import filters
from openedx.core.djangoapps.credentials_service.models import UserCredential, ProgramCertificate, CourseCertificate, \
    UserCredentialAttribute
from openedx.core.lib.api import parsers
from rest_framework import mixins, viewsets, parsers as drf_parsers

from rest_framework.response import Response
from rest_framework import status

log = logging.getLogger(__name__)


class UserCredentialViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    queryset = UserCredential.objects.all()
    lookup_field = 'username'
    serializer_class = serializers.UserCredentialSerializer
    parser_classes = (parsers.MergePatchParser,  drf_parsers.JSONParser)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /api/credentials/v1/users/{username}/
        Only to update the certificate status.
        """
        UserCredential.objects.filter(pk=request.data.get('id')).update(
            status=request.data.get('status')
        )

        return Response([], status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        # api/credentials/v1/programs/
        # {
        #     "credentials": [
        #       {
        #         "username": "user1",
        #         "program_id": 100,
        #         "attributes": [{
        #             "namespace": "white-list",
        #             "name": "grade",
        #             "value": "8.0"
        #         }]
        #      },
        #       {
        #         "username": "user2",
        #         "program_id": 100,
        #         "attributes": [{
        #             "namespace": "white-list",
        #             "name": "grade",
        #             "value": "10"
        #         }]
        #      }
        #     ]
        # }

        for credential in request.data.get('credentials'):

            program_id = credential.get('program_id')
            username = credential.get('username')
            attributes = credential.get('attributes')

            try:
                program = ProgramCertificate.objects.get(program_id=program_id)
            except:
                msg = (u'program id {id} not found').format(id=program_id)
                log.warning(msg)
                continue

            new_credential = UserCredential(username=username, credential=program)
            new_credential.save()

            attr_list = []
            for attr in attributes:
                attr_list.append(
                    UserCredentialAttribute(
                        user_credential=new_credential,
                        namespace=attr.get('namespace'),
                        name=attr.get('name'),
                        value=attr.get('value')
                    )
                )

            UserCredentialAttribute.objects.bulk_create(attr_list)

        return Response([], status=status.HTTP_200_OK)


class CredentialsByProgramsViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    lookup_field = 'program_id'
    queryset = ProgramCertificate.objects.all()
    serializer_class = serializers.ProgramCertificateSerializer

    parser_classes = (parsers.MergePatchParser,)



class CredentialsByCoursesViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
        mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):

    # TODO docstrings.

    lookup_field = 'course_id'
    queryset = CourseCertificate.objects.all()
    serializer_class = serializers.CourseCertificateSerializer

    parser_classes = (parsers.MergePatchParser,)


