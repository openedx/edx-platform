"""
    API for UserProfile model
"""

from edx_rest_framework_extensions.paginators import DefaultPagination
import edx_api_doc_tools as apidocs
from rest_framework import permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination


from common.djangoapps.student.models import (  # lint-amnesty, pylint: disable=unused-import
    User,
    UserProfile,
)
from .serializers import UserProfileSerializer


class UsersPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'


class UserProfileAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer
    pagination_class = UsersPagination
    queryset=''

    def get(self, request, pk=None):
        page = UsersPagination()
        if pk is not None:
            queryset = UserProfile.objects.get(pk=pk)
        else:
            queryset = UserProfile.objects.all()

        serializer = UserProfileSerializer(page.paginate_queryset(queryset, request), many=True)
        return Response(serializer.data)
