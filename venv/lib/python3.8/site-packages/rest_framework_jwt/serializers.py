# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.contrib.auth import authenticate, get_user_model

from rest_framework import serializers

from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework_jwt.compat import gettext_lazy as _
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import (
    check_payload,
    check_user,
    get_username_field,
    unix_epoch,
)


class JSONWebTokenSerializer(serializers.Serializer):
    """
    Serializer class used to validate a username and password.

    'username' is identified by the custom UserModel.USERNAME_FIELD.

    Returns a JSON Web Token that can be used to authenticate later calls.
    """

    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'})
    token = serializers.CharField(read_only=True)

    def __init__(self, *args, **kwargs):
        """Dynamically add the USERNAME_FIELD to self.fields."""
        super(JSONWebTokenSerializer, self).__init__(*args, **kwargs)

        self.fields[self.username_field
                    ] = serializers.CharField(write_only=True, required=True)

    @property
    def username_field(self):
        return get_username_field()

    def validate(self, data):
        credentials = {
            self.username_field: data.get(self.username_field),
            'password': data.get('password')
        }

        user = authenticate(self.context['request'], **credentials)

        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg)

        payload = JSONWebTokenAuthentication.jwt_create_payload(user)

        return {
            'token': JSONWebTokenAuthentication.jwt_encode_payload(payload),
            'user': user,
            'issued_at': payload.get('iat', unix_epoch())
        }


class VerifyAuthTokenSerializer(serializers.Serializer):
    """
    Serializer used for verifying JWTs.
    """

    token = serializers.CharField(required=True)

    def validate(self, data):
        token = data['token']

        payload = check_payload(token=token)
        user = check_user(payload=payload)

        return {
            'token': token,
            'user': user,
            'issued_at': payload.get('iat', None)
        }


class RefreshAuthTokenSerializer(serializers.Serializer):
    """
    Serializer used for refreshing JWTs.
    """

    token = serializers.CharField(required=True)

    def validate(self, data):
        token = data['token']

        payload = check_payload(token=token)
        user = check_user(payload=payload)

        # Get and check 'orig_iat'
        orig_iat = payload.get('orig_iat')

        if orig_iat is None:
            msg = _('orig_iat field not found in token.')
            raise serializers.ValidationError(msg)

        # Verify expiration
        refresh_limit = \
            api_settings.JWT_REFRESH_EXPIRATION_DELTA.total_seconds()

        expiration_timestamp = orig_iat + refresh_limit
        now_timestamp = unix_epoch()

        if now_timestamp > expiration_timestamp:
            msg = _('Refresh has expired.')
            raise serializers.ValidationError(msg)

        new_payload = JSONWebTokenAuthentication.jwt_create_payload(user)
        new_payload['orig_iat'] = orig_iat

        # Track the token ID of the original token, if it exists
        orig_jti = payload.get('orig_jti') or payload.get('jti')
        if orig_jti:
            new_payload['orig_jti'] = orig_jti
        elif api_settings.JWT_TOKEN_ID == 'require':
            msg = _('orig_jti or jti field not found in token.')
            raise serializers.ValidationError(msg)

        return {
            'token':
                JSONWebTokenAuthentication.jwt_encode_payload(new_payload),
            'user':
                user,
            'issued_at':
                new_payload.get('iat', unix_epoch())
        }


class ImpersonateAuthTokenSerializer(serializers.Serializer):
    """
    Serializer used for impersonation.
    """

    User = get_user_model()
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        fields = ("user", )

    def validate(self, data):
        user = data["user"]

        payload = JSONWebTokenAuthentication.jwt_create_payload(user)
        check_user(payload)

        token = JSONWebTokenAuthentication.jwt_encode_payload(payload)

        return {
            "user": user,
            "token": token,
            "issued_at": payload.get('iat', unix_epoch())
        }
