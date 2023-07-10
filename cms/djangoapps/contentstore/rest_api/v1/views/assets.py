# lint-amnesty, pylint: disable=missing-module-docstring
import logging
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from common.djangoapps.util.json_request import expect_json_in_class_view

from ....api import course_author_access_required

from cms.djangoapps.contentstore.asset_storage_handlers import handle_assets
import cms.djangoapps.contentstore.toggles as contentstore_toggles

log = logging.getLogger(__name__)
toggles = contentstore_toggles


@view_auth_classes()
class AssetsView(DeveloperErrorViewMixin, RetrieveUpdateDestroyAPIView, CreateAPIView):
    """
    public rest API endpoint for the Studio Content API.
    course_key_string: required argument, needed to authorize course authors.
    asset_key_string: required argument, needed to identify the asset.
    """

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
    def retrieve(self, request, course_key, asset_key_string):
        return handle_assets(request, course_key.html_id(), asset_key_string)

    @course_author_access_required
    @expect_json_in_class_view
    def update(self, request, course_key, asset_key_string):
        return handle_assets(request, course_key.html_id(), asset_key_string)

    @course_author_access_required
    @expect_json_in_class_view
    def destroy(self, request, course_key, asset_key_string):
        return handle_assets(request, course_key.html_id(), asset_key_string)

    @csrf_exempt
    @course_author_access_required
    @expect_json_in_class_view
    def create(self, request, course_key, asset_key_string):
        return handle_assets(request, course_key.html_id(), asset_key_string)
