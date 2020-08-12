""" Views that we will use to view toggle state in edx-platform. """
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.permissions import IsStaff

from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions, views
from rest_framework.response import Response


class ToggleStateView(views.APIView):
    """
    An endpoint for displaying the state of toggles in edx-platform.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsStaff,)

    def get(self, request):
        return Response("Hello")
