"""
Authn API Views
"""

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from common.djangoapps.student.helpers import get_next_url_for_login_page
from openedx.core.djangoapps.user_authn.views.utils import third_party_auth_context


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

    def get(self, request, **kwargs):  # lint-amnesty, pylint: disable=unused-argument
        """
        Returns the context for third party auth providers and the currently running pipeline.

        Arguments:
            request (HttpRequest): The request, used to determine if a pipeline
                is currently running.
            tpa_hint (string): An override flag that will return a matching provider
                as long as its configuration has been enabled
        """
        request_params = request.GET
        redirect_to = get_next_url_for_login_page(request)
        third_party_auth_hint = request_params.get('tpa_hint')

        context = third_party_auth_context(request, redirect_to, third_party_auth_hint)
        return Response(
            status=status.HTTP_200_OK,
            data=context
        )
