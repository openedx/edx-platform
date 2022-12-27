"""
Views for TwoU widget context in Learner Home
"""

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from edx_rest_framework_extensions.permissions import NotJwtRestrictedApplication
from ipware.ip import get_client_ip
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.djangoapps.learner_home.twou_widgets.serializers import (
    TwoUWidgetContextSerializer,
)
from openedx.core.djangoapps.geoinfo.api import country_code_from_ip


class TwoUWidgetContextView(APIView):
    """
    API to get the widget context i.e country code from the IP address.

    **Example Request**

    GET /api/learner_home/twou_widget_context/
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated, NotJwtRestrictedApplication)

    def get(self, request):
        """
        Retrieves the TwoU widget context.
        """
        user_ip_address = get_client_ip(request)[0]

        # Get country code from user IP address.
        country_code = country_code_from_ip(user_ip_address)

        return Response(
            TwoUWidgetContextSerializer(
                {
                    "countryCode": country_code,
                }
            ).data,
            status=200,
        )
