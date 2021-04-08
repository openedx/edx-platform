"""
Handle view-logic for the djangoapp
"""
from lti_consumer.models import LtiConfiguration
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.permissions import IsStaff
from openedx.core.lib.api.view_utils import view_auth_classes

from .models import DEFAULT_PROVIDER_TYPE
from .models import DiscussionsConfiguration


PROVIDER_FEATURE_MAP = {
    'legacy': [
        'discussion-page',
        'embedded-course-sections',
        'wcag-2.1',
    ],
    'piazza': [
        'discussion-page',
        'lti',
    ],
}


class LtiSerializer(serializers.ModelSerializer):
    """
    Serialize LtiConfiguration responses
    """
    class Meta:
        model = LtiConfiguration
        fields = [
            'lti_1p1_client_key',
            'lti_1p1_client_secret',
            'lti_1p1_launch_url',
            'version',
        ]

    def to_internal_value(self, data: dict) -> dict:
        """
        Transform the incoming primitive data into a native value
        """
        data = data or {}
        payload = {
            key: value
            for key, value in data.items()
            if key in self.Meta.fields
        }
        return payload

    def update(self, instance: LtiConfiguration, validated_data: dict) -> LtiConfiguration:
        """
        Create/update a model-backed instance
        """
        instance = instance or LtiConfiguration()
        instance.config_store = LtiConfiguration.CONFIG_ON_DB
        if validated_data:
            for key, value in validated_data.items():
                if key in self.Meta.fields:
                    setattr(instance, key, value)
            instance.save()
        return instance


@view_auth_classes()
class DiscussionsConfigurationView(APIView):
    """
    Handle configuration-related view-logic
    """
    permission_classes = (IsStaff,)

    class Serializer(serializers.ModelSerializer):
        """
        Serialize configuration responses
        """
        class Meta:
            model = DiscussionsConfiguration
            fields = [
                'context_key',
                'enabled',
                'provider_type',
            ]

        def to_internal_value(self, data: dict) -> dict:
            """
            Transform the *incoming* primitive data into a native value.
            """
            payload = {
                'context_key': data.get('course_key', ''),
                'enabled': data.get('enabled', False),
                'lti_configuration': data.get('lti_configuration', {}),
                'plugin_configuration': data.get('plugin_configuration', {}),
                'provider_type': data.get('provider_type', DEFAULT_PROVIDER_TYPE),
            }
            return payload

        def to_representation(self, instance: DiscussionsConfiguration) -> dict:
            """
            Serialize data into a dictionary, to be used as a response
            """
            payload = super().to_representation(instance)
            lti_configuration = LtiSerializer(instance.lti_configuration)
            payload.update({
                'features': {
                    'discussion-page',
                    'embedded-course-sections',
                    'lti',
                    'wcag-2.1',
                },
                'lti_configuration': lti_configuration.data,
                'plugin_configuration': instance.plugin_configuration,
                'providers': {
                    'active': instance.provider_type or DEFAULT_PROVIDER_TYPE,
                    'available': {
                        provider: {
                            'features': PROVIDER_FEATURE_MAP.get(provider) or [],
                        }
                        for provider in instance.available_providers
                    },
                },
            })
            return payload

        def update(self, instance: DiscussionsConfiguration, validated_data: dict) -> DiscussionsConfiguration:
            """
            Update and save an existing instance
            """
            keys = [
                'enabled',
                'plugin_configuration',
                'provider_type',
            ]
            for key in keys:
                value = validated_data.get(key)
                if value is not None:
                    setattr(instance, key, value)
            instance = self._update_lti(instance, validated_data)
            instance.save()
            return instance

        def _update_lti(self, instance: DiscussionsConfiguration, validated_data: dict) -> DiscussionsConfiguration:
            """
            Update LtiConfiguration
            """
            lti_configuration_data = validated_data.get('lti_configuration')
            if lti_configuration_data:
                instance.lti_configuration = instance.lti_configuration or LtiConfiguration()
                lti_configuration = LtiSerializer(
                    instance.lti_configuration,
                    data=lti_configuration_data,
                    partial=True,
                )
                if lti_configuration.is_valid(raise_exception=True):
                    lti_configuration.save()
            return instance

    # pylint: disable=redefined-builtin
    def get(self, request, course_key_string: str, **_kwargs) -> Response:
        """
        Handle HTTP/GET requests
        """
        course_key = self._validate_course_key(course_key_string)
        configuration = DiscussionsConfiguration.get(course_key)
        serializer = self.Serializer(configuration)
        return Response(serializer.data)

    def post(self, request, course_key_string: str, **_kwargs) -> Response:
        """
        Handle HTTP/POST requests

        TODO: Should we cleanup orphaned LTI config when swapping to cs_comments_service?
        """
        course_key = self._validate_course_key(course_key_string)
        configuration = DiscussionsConfiguration.get(course_key)
        serializer = self.Serializer(configuration, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data)

    def _validate_course_key(self, course_key_string: str) -> CourseKey:
        """
        Validate and parse a course_key string, if supported
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
        except InvalidKeyError as error:
            raise serializers.ValidationError(
                f"{course_key_string} is not a valid CourseKey"
            ) from error
        if course_key.deprecated:
            raise serializers.ValidationError(
                'Deprecated CourseKeys (Org/Course/Run) are not supported.'
            )
        return course_key
