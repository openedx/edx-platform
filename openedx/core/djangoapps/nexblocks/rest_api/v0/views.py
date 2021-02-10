
from edx_rbac.mixins import PermissionRequiredMixin
from rest_framework import permissions, status, viewsets
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from rest_framework.views import APIView
from openedx.core.djangoapps.nexblocks.xblock import NexBlockWrapperBlock
from opaque_keys.edx.keys import UsageKey
from rest_framework.response import Response
from django.contrib.auth.decorators import login_required

from xmodule.modulestore.django import modulestore

class NexBlockInstanceDataView(APIView):
    authentication_classes = (
        JwtAuthentication,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        usage_key = request.GET.get('usage_key')
        try:
            block = modulestore().get_item(UsageKey.from_string(usage_key))
            if block.display_name == 'NexBlock':
                if block.instance_data:
                    return instance_data
                else:
                    return Response(status=status.HTTP_404_NOT_FOUND)
            else:
                message = 'Provided block is not a NexBlock'
                return Response(status=status.HTTP_400_BAD_REQUEST, data={'message': message})
            return Response(status=status.HTTP_200_OK, data=instance_data)
        except Exception:
            raise
