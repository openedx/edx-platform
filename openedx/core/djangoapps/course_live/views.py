from typing import Dict

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from lti_consumer.api import get_lti_pii_sharing_state_for_course
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView

from common.djangoapps.util.views import ensure_valid_course_key
from openedx.core.djangoapps.course_live.permissions import IsStaffOrInstructor
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser

from .models import AVAILABLE_PROVIDERS, CourseLiveConfiguration
from .serializers import CourseLiveConfigurationSerializer


class CourseLiveConfigurationView(APIView):
    """
    View for configuring discussion settings.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsStaffOrInstructor,)

    @ensure_valid_course_key
    def get(self, request: Request, course_key_string: str) -> Response:
        """
        Handle HTTP/GET requests
        """
        pii_sharing_allowed = get_lti_pii_sharing_state_for_course(course_key_string)
        if not pii_sharing_allowed:
            return Response({
                "pii_sharing_allowed" : pii_sharing_allowed,
                "message" : "PII sharing is not allowed on this course"
            })

        configuration = CourseLiveConfiguration.get(course_key_string)
        serializer = CourseLiveConfigurationSerializer(configuration, context= {
            "pii_sharing_allowed": pii_sharing_allowed,
        })

        return Response(serializer.data)



    @ensure_valid_course_key
    def post(self, request, course_key_string: str) -> Response:
        """
        Handle HTTP/POST requests
        """
        pii_sharing_allowed = get_lti_pii_sharing_state_for_course(course_key_string)
        if not pii_sharing_allowed:
            return Response({
                "pii_sharing_allowed": pii_sharing_allowed,
                "message": "PII sharing is not allowed on this course"
            })

        configuration = CourseLiveConfiguration.get(course_key_string)
        serializer = CourseLiveConfigurationSerializer(
            configuration,
            data=request.data,
            context={
                "pii_sharing_allowed": pii_sharing_allowed,
                "course_key_string" : course_key_string
            }
        )
        if not serializer.is_valid():
            raise ValidationError(dict(list(serializer.errors.items())))
        serializer.save()
        return Response(serializer.data)


class CourseLiveProvidersView(APIView):
    """
    Read only view that lists details of LIVE providers available for a course.
    """
    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser
    )
    permission_classes = (IsStaffOrInstructor,)

    @ensure_valid_course_key
    def get(self, request, course_key_string: str, **_kwargs) -> Response:
        """
        Handle HTTP/GET requests
        """
        data = self.get_provider_data(course_key_string)
        return Response(data)

    @staticmethod
    def get_provider_data(course_key_string: str) -> Dict:
        """
        Get provider data for specified course
        Args:
            course_key_string (str): course key string

        Returns:
            Dict: course discussion providers
        """
        configuration = CourseLiveConfiguration.get(course_key_string)
        return {
            "providers": {
                "active": configuration.provider_name,
                "available": AVAILABLE_PROVIDERS
            }
        }
