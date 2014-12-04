from rest_framework import generics
from rest_framework.views import APIView
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.lib.api.serializers import PaginationSerializer


class PermissionMixin(object):
    """
    Mixin to set custom permission_classes
    """
    permission_classes = (ApiKeyHeaderPermission,)


class APIViewWithPermissions(PermissionMixin, APIView):
    """
    View used for protecting access to specific workflows
    """
    pass


class PaginatedListAPIViewWithPermissions(PermissionMixin, generics.ListAPIView):
    """ Inherited from ListAPIView """
    paginate_by = 10
    paginate_by_param = 'page_size'
    pagination_serializer_class = PaginationSerializer
