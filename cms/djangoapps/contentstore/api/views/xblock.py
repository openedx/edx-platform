# lint-amnesty, pylint: disable=missing-module-docstring
import logging
import time

import numpy as np
from edxval.api import get_videos_for_course
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from scipy import stats
from django.http import Http404, HttpResponse, HttpResponseBadRequest

from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from openedx.core.lib.cache_utils import request_cached
from openedx.core.lib.graph_traversals import traverse_pre_order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from common.djangoapps.util.json_request import JsonResponse, expect_json_in_class_view

from .utils import course_author_access_required, get_bool_param

from cms.djangoapps.contentstore.views.block import usage_key_with_run, modify_xblock, handle_xblock

log = logging.getLogger(__name__)

@view_auth_classes()
class XblockView(DeveloperErrorViewMixin, UpdateAPIView):
    @course_author_access_required
    @expect_json_in_class_view
    def update(self, request, course_key, usage_key_string=None):
        response = handle_xblock(request, usage_key_string)

        print(response)
        return response
