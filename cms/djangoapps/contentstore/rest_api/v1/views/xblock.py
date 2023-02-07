# lint-amnesty, pylint: disable=missing-module-docstring
import logging
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from django.views.decorators.csrf import csrf_exempt

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required

from cms.djangoapps.contentstore.xblock_services.xblock_service import handle_xblock

log = logging.getLogger(__name__)


@view_auth_classes()
class XblockView(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView, CreateAPIView):

    @course_author_access_required
    @expect_json_in_class_view
    def retrieve(self, request, course_key, usage_key_string=None):
        response = handle_xblock(request, usage_key_string)

        print(response)
        return response

    @course_author_access_required
    @expect_json_in_class_view
    def update(self, request, course_key, usage_key_string=None):
        response = handle_xblock(request, usage_key_string)

        print(response)
        return response

    @course_author_access_required
    @expect_json_in_class_view
    def partial_update(self, request, course_key, usage_key_string=None):
        response = handle_xblock(request, usage_key_string)

        print(response)
        return response

    @course_author_access_required
    @expect_json_in_class_view
    def destroy(self, request, course_key, usage_key_string=None):
        response = handle_xblock(request, usage_key_string)

        print(response)
        return response

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    def create(self, request, course_key, usage_key_string=None):
        response = handle_xblock(request, usage_key_string)

        print(response)
        return response
