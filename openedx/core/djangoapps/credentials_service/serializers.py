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
        elif isinstance(value, CourseCertificate):
            return {
                'course_id': value.course_id,
                'certificate_type': value.certificate_type
            }


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """ User Credential Attribute Serializer """
    class Meta(object):
        model = UserCredentialAttribute
        fields = ('user_credential', 'namespace', 'name', 'value')


class UserCredentialSerializer(serializers.ModelSerializer):
    """ User Credential Serializer """

    credential = CredentialRelatedField(read_only='True')
    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)

    class Meta(object):
        model = UserCredential
        fields = (
            'id', 'username', 'credential_id', 'credential',
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


class CourseCertificateBaseSerializer(serializers.ModelSerializer):
    """ User Credential Attribute Serializer """
    class Meta(object):
        model = CourseCertificate
        fields = ('course_id', 'certificate_type', )


class CourseCertificateSerializer(ProgramCertificateBaseSerializer):
    """ User Credential Attribute Serializer """
    user_credential = serializers.SerializerMethodField("get_users")

    class Meta(object):
        model = CourseCertificate
        fields = ('user_credential', 'course_id', 'certificate_type',)


    def get_users(self, course):
        return UserCredentialSerializer(course.user_credentials.all(), many=True).data
