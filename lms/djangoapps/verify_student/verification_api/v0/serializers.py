# pylint: disable=missing-docstring

from rest_framework import serializers

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification


class SoftwareSecurePhotoVerificationSerializer(serializers.ModelSerializer):
    expires = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.username

    def get_expires(self, obj):
        return obj.expiration_datetime

    class Meta(object):
        fields = ('username', 'status', 'expires',)
        model = SoftwareSecurePhotoVerification
