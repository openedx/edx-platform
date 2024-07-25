from rest_framework import generics, status
from rest_framework.response import Response

from .. import permissions

class GetProblemResponseViewset(generics.GenericAPIView):
    permission_classes = (
          permissions.CAN_RESEARCH,
    )
    http_method_names = ["post"]

    def get(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)
        