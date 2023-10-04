"""
Public rest API endpoints for the CMS API Assets.
"""
import logging
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, DestroyAPIView
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required

from cms.djangoapps.contentstore.asset_storage_handlers import handle_assets
import cms.djangoapps.contentstore.toggles as contentstore_toggles

from cms.djangoapps.contentstore.rest_api.v1.serializers import AssetSerializer
from .utils import validate_request_with_serializer
from rest_framework.parsers import (MultiPartParser, FormParser, JSONParser)
from openedx.core.lib.api.parsers import TypedFileUploadParser

log = logging.getLogger(__name__)
toggles = contentstore_toggles


@view_auth_classes()
class AssetsCreateRetrieveView(DeveloperErrorViewMixin, CreateAPIView, RetrieveAPIView):
    """
    public rest API endpoints for the CMS API Assets.
    course_key: required argument, needed to authorize course authors and identify the asset.
    asset_key_string: required argument, needed to identify the asset.
    """
    serializer_class = AssetSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser, TypedFileUploadParser)

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @csrf_exempt
    @course_author_access_required
    @validate_request_with_serializer
    def create(self, request, course_key):  # pylint: disable=arguments-differ
        return handle_assets(request, course_key.html_id())

    @course_author_access_required
    @expect_json_in_class_view
    def retrieve(self, request, course_key):  # pylint: disable=arguments-differ
        return handle_assets(request, course_key.html_id())


@view_auth_classes()
class AssetsUpdateDestroyView(DeveloperErrorViewMixin, UpdateAPIView, DestroyAPIView):
    """
    public rest API endpoints for the CMS API Assets.
    course_key: required argument, needed to authorize course authors and identify the asset.
    asset_key_string: required argument, needed to identify the asset.
    """
    serializer_class = AssetSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser, TypedFileUploadParser)

    def dispatch(self, request, *args, **kwargs):
        # TODO: probably want to refactor this to a decorator.
        """
        The dispatch method of a View class handles HTTP requests in general
        and calls other methods to handle specific HTTP methods.
        We use this to raise a 404 if the content api is disabled.
        """
        if not toggles.use_studio_content_api():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    @course_author_access_required
    @expect_json_in_class_view
    @validate_request_with_serializer
    def update(self, request, course_key, asset_key_string):  # pylint: disable=arguments-differ
        return handle_assets(request, course_key.html_id(), asset_key_string)

    @course_author_access_required
    @expect_json_in_class_view
    def destroy(self, request, course_key, asset_key_string):  # pylint: disable=arguments-differ
        return handle_assets(request, course_key.html_id(), asset_key_string)
