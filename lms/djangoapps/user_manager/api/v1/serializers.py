from rest_framework import fields, serializers

from ...utils import create_user_manager_role


class ManagerListSerializer(serializers.Serializer):  # pylint: disable=abstract-method
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


class ManagerReportsSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """ Serializer for User manager reports """

    email = fields.EmailField(source='user.email')
    id = fields.IntegerField(source='user.id', required=False)

    def create(self, validated_data):
        user = validated_data.get('user')
        manager_user = validated_data.get('manager_user')
        unregistered_manager_email = validated_data.get('unregistered_manager_email')
        return create_user_manager_role(user, manager_user, unregistered_manager_email)


class UserManagerSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """ Serializer for User manager reports """

    email = fields.EmailField(source='manager_email')
    id = fields.IntegerField(source='user_manager.id', required=False)

    def create(self, validated_data):
        user = validated_data.get('user')
        manager_user = validated_data.get('manager_user')
        unregistered_manager_email = validated_data.get('unregistered_manager_email')
        return create_user_manager_role(user, manager_user, unregistered_manager_email)
