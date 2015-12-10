"""
Serializers for data manipulated by the credentials service APIs.
"""
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from openedx.core.djangoapps.credentials_service.models import UserCredential, AbstractCredential, \
    UserCredentialAttribute, ProgramCertificate, CourseCertificate


class AbstractCredentialSerializer(serializers.ModelSerializer):
    """ Abstract Credential Serializer """
    class Meta(object):
        model = AbstractCredential


class CredentialRelatedFieldRelatedField(serializers.RelatedField):
    """
    A custom field to use for the user credential generic relationship.
    """
    def to_representation(self, value):
        """
        Serialize objects to a simple textual representation.
        """
        if isinstance(value, ProgramCertificate):
            return {
                'credential_type': 'program-certificate',
                'program-certificate': value.program_id
            }
        elif isinstance(value, CourseCertificate):
            return {
                'credential_type': 'course-certificate',
                'certificate_type': value.certificate_type,
                'course-certificate': value.course_id,
            }
        raise Exception('Unexpected type of tagged object')


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """ Abstract Credential Serializer """
    class Meta(object):
        model = UserCredentialAttribute
        fields = ('user_credential', 'namespace', 'name', 'value')


class UserCredentialSerializer(serializers.ModelSerializer):
    """ User Credential Serializer """

    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)
    credential = CredentialRelatedFieldRelatedField(read_only='True')

    class Meta(object):
        model = UserCredential
        fields = ('username', 'credential_id', 'credential', 'status', 'download_url', 'uuid'
                  , 'attributes')
