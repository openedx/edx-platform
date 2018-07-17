from django.contrib.auth.models import User
from rest_framework import fields, serializers


class UserManagerSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """ Serializer for User manager """

    email = fields.SerializerMethodField()
    id = fields.SerializerMethodField()

    def get_email(self, obj):
        if obj["manager_user"] is not None:
            return obj["manager_user__email"]
        else:
            return obj["unregistered_manager_email"]

    def get_id(self, obj):
        return obj["manager_user"]

    class Meta(object):
        fields = ('email', 'id')


class UserManagerReportsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """ Serializer for User manager reports """

    email = fields.CharField(source='user.email')
    id = fields.IntegerField(source='user.id')

    class Meta(object):
        fields = ('email', 'id')
