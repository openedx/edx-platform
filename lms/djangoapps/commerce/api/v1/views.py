"""
Commerce views
"""


import logging

from django.contrib.auth.models import User
from django.http import Http404
from edx_rest_api_client import exceptions
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from openedx.core.lib.api.authentication import BearerAuthentication

from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.lib.api.mixins import PutAsCreateMixin
from common.djangoapps.util.json_request import JsonResponse

from ...utils import is_account_activation_requirement_disabled
from .models import Course
from .permissions import ApiKeyOrModelPermission, IsAuthenticatedOrActivationOverridden
from .serializers import CourseSerializer

log = logging.getLogger(__name__)


class CourseListView(ListAPIView):
    """ List courses and modes. """
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseSerializer
    pagination_class = None

    def get_queryset(self):
        return list(Course.iterator())


class CourseRetrieveUpdateView(PutAsCreateMixin, RetrieveUpdateAPIView):
    """ Retrieve, update, or create courses/modes. """
    lookup_field = 'id'
    lookup_url_kwarg = 'course_id'
    model = CourseMode
    authentication_classes = (JwtAuthentication, BearerAuthentication, SessionAuthentication,)
    permission_classes = (ApiKeyOrModelPermission,)
    serializer_class = CourseSerializer

    # Django Rest Framework v3 requires that we provide a queryset.
    # Note that we're overriding `get_object()` below to return a `Course`
    # rather than a CourseMode, so this isn't really used.
    queryset = CourseMode.objects.all()

    def get_object(self, queryset=None):
        course_id = self.kwargs.get(self.lookup_url_kwarg)
        course = Course.get(course_id)

        if course:
            return course

        raise Http404

    def pre_save(self, obj):
        # There is nothing to pre-save. The default behavior changes the Course.id attribute from
        # a CourseKey to a string, which is not desired.
        pass


class OrderView(APIView):
    """ Retrieve order details. """

    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (IsAuthenticatedOrActivationOverridden,)

    def get(self, request, number):
        """ HTTP handler. """
        # If the account activation requirement is disabled for this installation, override the
        # anonymous user object attached to the request with the actual user object (if it exists)
        if not request.user.is_authenticated and is_account_activation_requirement_disabled():
            try:
                request.user = User.objects.get(id=request.session._session_cache['_auth_user_id'])
            except User.DoesNotExist:
                return JsonResponse(status=403)
        try:
            order = ecommerce_api_client(request.user).orders(number).get()
            return JsonResponse(order)
        except exceptions.HttpNotFoundError:
            return JsonResponse(status=404)
