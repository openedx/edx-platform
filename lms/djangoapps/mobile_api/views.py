"""
Views for the mobile API.
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from lms.djangoapps.mobile_api.models import MobileConfig


class MobileConfigurationView(APIView):
    """
    API endpoint that returns mobile configuration data.
    """

    def get(self, request, *args, **kwargs):
        """
        Get all mobile configurations.
        """
        return Response(MobileConfig.get_structured_configs())
