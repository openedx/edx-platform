"""
Handle view-logic for the djangoapp
"""
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.lib.api.permissions import IsStaff
from openedx.core.lib.api.view_utils import view_auth_classes

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


@view_auth_classes()
class DiscussionsConfigurationView(APIView):
    """
    Handle configuration-related view-logic
    """
    permission_classes = (IsStaff,)

    class Serializer(serializers.BaseSerializer):
        """
        Serialize configuration responses
        """

        def create(self, validated_data):
            """
            Create and save a new instance
            """
            raise NotImplementedError

        def to_internal_data(self, data):
            """
            Transform the *incoming* primitive data into a native value.
            """
            raise NotImplementedError

        def to_representation(self, instance) -> dict:
            """
            Serialize data into a dictionary, to be used as a response
            """
            payload = {
                'context_key': str(instance.context_key),
                'enabled': instance.enabled,
                'features': {
                    'discussion-page',
                    'embedded-course-sections',
                    'lti',
                    'wcag-2.1',
                },
                'plugin_configuration': instance.plugin_configuration,
                'providers': {
                    'active': instance.provider_type or None,
                    'available': {
                        provider: {
                            'features': PROVIDER_FEATURE_MAP.get(provider) or [],
                        }
                        for provider in instance.available_providers
                    },
                },
            }
            return payload

        def update(self, instance, validated_data):
            """
            Update and save an existing instance
            """
            raise NotImplementedError

    # pylint: disable=redefined-builtin
    def get(self, request, course_key_string, **_kwargs) -> Response:
        """
        Handle HTTP/GET requests
        """
        course_key = self._validate_course_key(course_key_string)
        configuration = DiscussionsConfiguration.get(course_key)
        serializer = self.Serializer(configuration)
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
