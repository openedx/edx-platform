"""
Serializers for data manipulated by the credentials service APIs.
"""
from rest_framework import serializers

from openedx.core.djangoapps.credentials_service.models import UserCredential, UserCredentialAttribute, \
    ProgramCertificate, CourseCertificate


class CredentialRelatedField(serializers.RelatedField):
    """
    A custom field to use for the user credential generic relationship.
    """

    def to_representation(self, value):
        """
        Serialize objects to a according to model content-type.
        """
        if isinstance(value, ProgramCertificate):
            return {
                'program_id': value.program_id
            }
        elif isinstance(value, CourseCertificate):
            return {
                'course_id': value.course_id,
                'certificate_type': value.certificate_type
            }


class UserCredentialAttributeSerializer(serializers.ModelSerializer):
    """ Serializer for CredentialAttribute objects """

    class Meta(object):
        model = UserCredentialAttribute
        fields = ('namespace', 'name', 'value')


class UserCredentialSerializer(serializers.ModelSerializer):
    """ Serializer for User Credential objects. """

    credential = CredentialRelatedField(read_only='True')
    attributes = UserCredentialAttributeSerializer(many=True, read_only=True)

    class Meta(object):
        model = UserCredential
        fields = (
            'id', 'username', 'credential',
            'status', 'download_url', 'uuid', 'attributes'
        )
        paginate_by = 10
        paginate_by_param = "page_size"


class ProgramCertificateBaseSerializer(serializers.ModelSerializer):
    """ Base serializer for ProgramCertificate objects. """

    class Meta(object):
        model = ProgramCertificate
        fields = ('program_id',)


class ProgramCertificateSerializer(ProgramCertificateBaseSerializer):
    """ Serializer for ProgramCertificate objects. """
    user_credential = serializers.SerializerMethodField("get_users")

    class Meta(ProgramCertificateBaseSerializer.Meta):
        fields = ('user_credential', 'program_id')

    def get_users(self, program):
        """ Returns all user credential for given program. """
        return UserCredentialSerializer(program.user_credentials.all(), many=True).data


class CourseCertificateBaseSerializer(serializers.ModelSerializer):
    """ Base serializer for CourseCertificate objects. """

    class Meta(object):
        model = CourseCertificate
        fields = ('course_id', 'certificate_type', )


class CourseCertificateSerializer(CourseCertificateBaseSerializer):
    """ Serializer for CourseCertificate objects. """
    user_credential = serializers.SerializerMethodField("get_users")

    class Meta(CourseCertificateBaseSerializer.Meta):
        model = CourseCertificate
        fields = ('user_credential', 'course_id', 'certificate_type',)

    def get_users(self, course):
        """ Returns all user credential for given course. """
        return UserCredentialSerializer(course.user_credentials.all(), many=True).data
