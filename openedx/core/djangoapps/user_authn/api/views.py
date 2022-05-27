"""
Authn API Views
"""

from django.conf import settings

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from common.djangoapps.student.helpers import get_next_url_for_login_page
from common.djangoapps.student.views import compose_and_send_activation_email
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_authn.api.helper import RegistrationFieldsContext
from openedx.core.djangoapps.user_authn.views.utils import get_mfe_context
from openedx.core.lib.api.authentication import BearerAuthentication


class MFEContextThrottle(AnonRateThrottle):
    """
    Setting rate limit for MFEContextView API
    """
    rate = settings.LOGISTRATION_API_RATELIMIT


class MFEContextView(RegistrationFieldsContext):
    """
    API to get third party auth providers, user country code and the currently running pipeline.
    """
    FIELD_TYPE = 'required'
    throttle_classes = [MFEContextThrottle]

    def get(self, request, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns
        - dynamic registration fields
        - the context for third party auth providers
        - user country code
        - the currently running pipeline.

        Arguments:
            request (HttpRequest): The request, used to determine if a pipeline
                is currently running.
            tpa_hint (string): An override flag that will return a matching provider
                as long as its configuration has been enabled
        """
        request_params = request.GET
        redirect_to = get_next_url_for_login_page(request)
        third_party_auth_hint = request_params.get('tpa_hint')

        context = {
            'context_data': get_mfe_context(request, redirect_to, third_party_auth_hint),
            'registration_fields': {},
        }

        if settings.ENABLE_DYNAMIC_REGISTRATION_FIELDS:
            registration_fields = self._get_fields()
            context['registration_fields'].update({
                'fields': registration_fields,
                'extended_profile': configuration_helpers.get_value('extended_profile_fields', []),
            })

        return Response(
            status=status.HTTP_200_OK,
            data=context
        )


class SendAccountActivationEmail(APIView):
    """
    API to to send the account activation email using account activation cta.
    """
    authentication_classes = (SessionAuthenticationAllowInactiveUser,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns status code.
        Arguments:
            request (HttpRequest): The request, used to get the user
        """
        try:
            user = request.user
            if not user.is_active:
                compose_and_send_activation_email(user, user.profile)
            return Response(
                status=status.HTTP_200_OK
            )
        except Exception:  # pylint: disable=broad-except
            return Response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OptionalFieldsThrottle(UserRateThrottle):
    """
    Setting rate limit for OptionalFieldsData API
    """
    rate = settings.OPTIONAL_FIELD_API_RATELIMIT


class OptionalFieldsView(RegistrationFieldsContext):
    """
    Construct Registration forms and associated fields.
    """
    FIELD_TYPE = 'optional'

    throttle_classes = [OptionalFieldsThrottle]
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns Optional fields to be shown on Progressive Profiling page
        """
        response = self._get_fields()
        if not self.valid_fields or not response:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'error_code': f'{self.FIELD_TYPE}_fields_configured_incorrectly'}
            )

        return Response(
            status=status.HTTP_200_OK,
            data={
                'fields': response,
                'extended_profile': configuration_helpers.get_value('extended_profile_fields', []),
            },
        )
