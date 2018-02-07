import logging

from django.contrib.auth.models import User
from django.http import Http404
from edx_rest_api_client import exceptions
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.views import APIView

from course_modes.models import CourseMode
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.core.lib.api.mixins import PutAsCreateMixin
from openedx.core.lib.api.view_utils import view_auth_classes
from util.json_request import JsonResponse

from ...utils import is_account_activation_requirement_disabled
from .models import Course
from .permissions import ApiKeyOrModelPermission, IsAuthenticatedOrActivationOverridden
from .serializers import CourseSerializer

log = logging.getLogger(__name__)


@view_auth_classes()
class CourseListView(ListAPIView):
    """ List courses and modes. """
    serializer_class = CourseSerializer
    pagination_class = None

    def get_queryset(self):
        return list(Course.iterator())


@view_auth_classes(is_authenticated=False, permission_classes=(ApiKeyOrModelPermission,))
class CourseRetrieveUpdateView(PutAsCreateMixin, RetrieveUpdateAPIView):
    """ Retrieve, update, or create courses/modes. """
    lookup_field = 'id'
    lookup_url_kwarg = 'course_id'
    model = CourseMode
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


@view_auth_classes(is_authenticated=False, permission_classes=(IsAuthenticatedOrActivationOverridden,))
class OrderView(APIView):
    """ Retrieve order details. """

    def get(self, request, number):
        """ HTTP handler. """
        # If the account activation requirement is disabled for this installation, override the
        # anonymous user object attached to the request with the actual user object (if it exists)
        if not request.user.is_authenticated() and is_account_activation_requirement_disabled():
            try:
                request.user = User.objects.get(id=request.session._session_cache['_auth_user_id'])
            except User.DoesNotExist:
                return JsonResponse(status=403)
        try:
            order = ecommerce_api_client(request.user).orders(number).get()
            return JsonResponse(order)
        except exceptions.HttpNotFoundError:
            return JsonResponse(status=404)
