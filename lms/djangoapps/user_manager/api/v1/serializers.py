from rest_framework import fields, serializers

from lms.djangoapps.user_manager.models import UserManagerRole


class UserManagerSerializerBase(serializers.Serializer):
    class Meta(object):
        fields = ('email', 'id')

    def create(self, validated_data):
        user = validated_data.get('user')
        manager_user = validated_data.get('manager_user')
        unregistered_manager_email = validated_data.get('unregistered_manager_email')

        if unregistered_manager_email is not None:
            return UserManagerRole.objects.create(
                unregistered_manager_email=unregistered_manager_email,
                user=user,
            )

        return UserManagerRole.objects.create(
            manager_user=manager_user,
            user=user
        )


class ManagerListSerializer(UserManagerSerializerBase):  # pylint: disable=abstract-method
    """ Serializer for User manager """

    email = fields.SerializerMethodField()
    id = fields.SerializerMethodField()

    class Meta(object):
        fields = ('email', 'id')

    def get_email(self, obj):
        if obj["manager_user"] is not None:
            return obj["manager_user__email"]
        else:
            return obj["unregistered_manager_email"]

    def get_id(self, obj):
        return obj["manager_user"]


class ManagerReportsSerializer(UserManagerSerializerBase):  # pylint: disable=abstract-method
    """ Serializer for User manager reports """

    email = fields.CharField(source='user.email')
    id = fields.IntegerField(source='user.id', required=False)


class UserManagerSerializer(UserManagerSerializerBase):  # pylint: disable=abstract-method
    """ Serializer for User manager reports """

    email = fields.CharField(source='get_manager_email')
    id = fields.IntegerField(source='user_manager.id', required=False)
