"""
Logistration API Views
"""

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from openedx.core.djangoapps.user_authn.utils import third_party_auth_context

REDIRECT_KEY = 'redirect_to'


class ThirdPartyAuthContextThrottle(AnonRateThrottle):
    """
    Setting rate limit for ThirdPartyAuthContext API
    """
    rate = settings.LOGISTRATION_API_RATELIMIT


class TPAContextView(APIView):
    """
    API to get third party auth providers and the currently running pipeline.
    """
    throttle_classes = [ThirdPartyAuthContextThrottle]

    def get(self, request, **kwargs):
        """
        Returns the context for third party auth providers and the currently running pipeline.

        Arguments:
            request (HttpRequest): The request, used to determine if a pipeline
                is currently running.
            redirect_to: The URL to send the user to following successful
                authentication.
            tpa_hint (string): An override flag that will return a matching provider
                as long as its configuration has been enabled
        """
        request_params = request.GET

        if REDIRECT_KEY not in request_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={'message': 'Request missing required parameter: {}'.format(REDIRECT_KEY)}
            )

        redirect_to = request_params.get(REDIRECT_KEY)
        third_party_auth_hint = request_params.get('tpa_hint')

        context = third_party_auth_context(request, redirect_to, third_party_auth_hint)
        return Response(
            status=status.HTTP_200_OK,
            data=context
        )
