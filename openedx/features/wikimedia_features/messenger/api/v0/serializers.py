"""
Serializers for Messenger v0 API(s)
"""
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework import serializers
from openedx.features.wikimedia_features.messenger.models import Inbox, Message
from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_urls_for_user


def validate_username(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        raise serializers.ValidationError(_('User does not exist - invalid username {}'.format(username)))


class StringListField(serializers.ListField):
    child = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username',)

class BulkMessageSerializer(serializers.Serializer):
    receivers = StringListField()
    message = serializers.CharField()

    def validate_receivers(self, receivers):
        if not receivers:
            raise serializers.ValidationError(_('receiver list can not empty.'))
        users = [validate_username(username) for username in receivers]
        return users

    def bulk_create(self, request=None):
        created_messages = []
        if not request:
            raise serializers.ValidationError(_('Missing request object.'))
        receivers = self.validated_data.get('receivers')
        message = self.validated_data.get('message')
        with transaction.atomic():
            for user in receivers:
                created_messages.append(
                    Message.objects.create(sender=request.user, receiver=user, message=message)
                )
        return created_messages


class InboxSerializer(serializers.ModelSerializer):
    with_user = serializers.SerializerMethodField()
    request = None

    class Meta:
        model = Inbox
        fields = ('id', 'with_user', 'last_message', 'unread_count')

    def __init__(self, *args, **kwargs):
        super(InboxSerializer, self).__init__(*args, **kwargs)
        self.request = self.context.get('request')

    def get_with_user(self, obj):
        if self.request:
            if obj.last_message.sender != self.request.user:
                return obj.last_message.sender.username
            return obj.last_message.receiver.username
        raise serializers.ValidationError(
            _('Invalid request - request object not found.')
        )

    def to_representation(self, instance):
        response = super().to_representation(instance)
        with_user = User.objects.get(username=response.get('with_user'))
        response['with_user_img'] = get_profile_image_urls_for_user(with_user, self.request).get('medium')
        response['last_message'] = instance.last_message.message
        response['last_message_date'] = instance.last_message.created.strftime('%x')

        # if last message is send by login-user then unread count will be 0
        if self.request and instance.last_message.sender == self.request.user:
            response['unread_count'] = 0

        return response


class MessageSerializer(serializers.ModelSerializer):
    receiver = serializers.CharField(source='receiver.username')
    class Meta:
        model = Message
        fields = ('id', 'sender', 'receiver', 'message', 'created')
        read_only_fields = ('id', 'created', 'sender')

    def validate_receiver(self, receiver):
        return validate_username(receiver)

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        validated_data['receiver'] = validated_data.get('receiver', {}).get('username')
        return super().create(validated_data)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['sender'] = instance.sender.username
        response['created'] = instance.created.strftime('%x %I:%M %p')
        response['sender_img']= get_profile_image_urls_for_user(
            instance.sender, self.context.get('request')
        ).get('medium')
        return response
