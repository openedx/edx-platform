"""
.
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from opaque_keys.edx.keys import UsageKey
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.nexblocks.xblock import NexBlockWrapperBlock
from xmodule.modulestore.django import modulestore

from ...xblock import NexBlockWrapperBlock


class NexBlockInstanceDataView(APIView):
    """
    .
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, usage_id=None):
        """
        handle GET
        """
        block = modulestore().get_item(UsageKey.from_string(usage_id))
        if isinstance(block, NexBlockWrapperBlock):
            return Response(data=block.instance_data)
        else:
            message = "Provided block is not a NexBlock"
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"message": message}
            )
