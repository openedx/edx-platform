"""
Serializers for data manipulated by the credentials service APIs.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from openedx.core.djangoapps.credentials_service.models import UserCredential, AbstractCredential, \
    UserCredentialAttribute, ProgramCertificate, CourseCertificate


class CredentialRelatedField(serializers.RelatedField):
    """
    A custom field to use for the user credential generic relationship.
    """
    def to_representation(self, value):
        """
        Serialize objects to a simple textual representation.
        """
        if isinstance(value, ProgramCertificate):
            return value.program_id
            # return ProgramCertificateBaseSerializer(value).data


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """ User Credential Attribute Serializer """
    class Meta(object):
        model = UserCredentialAttribute
        fields = ('user_credential', 'namespace', 'name', 'value')


class UserCredentialSerializer(serializers.ModelSerializer):
    """ User Credential Serializer """

    credential_object = CredentialRelatedField(read_only='True')
    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)

    class Meta(object):
        model = UserCredential
        fields = (
            'username', 'object_id', 'credential_object',
            'status', 'download_url', 'uuid', 'attributes'
        )


class ProgramCertificateBaseSerializer(serializers.ModelSerializer):
    """ User Credential Attribute Serializer """
    class Meta(object):
        model = ProgramCertificate
        fields = ('program_id',)


class ProgramCertificateSerializer(ProgramCertificateBaseSerializer):
    """ User Credential Attribute Serializer """
    user_credential = serializers.SerializerMethodField("get_users")

    class Meta(object):
        model = ProgramCertificate
        fields = ('user_credential', 'program_id')

    def get_users(self, program):
        return UserCredentialSerializer(program.user_credentials.all(), many=True).data
