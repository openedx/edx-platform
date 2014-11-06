import logging
from functools import partial
import math
import json

from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.conf import settings

from edxmako.shortcuts import render_to_response
from cache_toolbox.core import del_cached_content

from contentstore.utils import reverse_course_url
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.content import StaticContent
from xmodule.exceptions import NotFoundError
from django.core.exceptions import PermissionDenied
from opaque_keys.edx.keys import CourseKey, AssetKey

from util.date_utils import get_default_time_display
from util.json_request import JsonResponse
from django.http import HttpResponseNotFound
from django.utils.translation import ugettext as _
from pymongo import ASCENDING, DESCENDING
from .access import has_course_access
from xmodule.modulestore.exceptions import ItemNotFoundError

__all__ = ['videos_list_handler']


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
def videos_list_handler(request, course_key_string=None):
    """
    The restful handler for videos.
    It allows bulk upload of course vidoes, as well as listing of uploaded assets.

    GET
        html: return an html page which will show all uploaded course videos. Note that only the video container
            is returned and that the actual assets are filled in with a client-side request.
        json: returns a page of assets. The following parameters are supported:
            page: the desired page of results (defaults to 0)
            page_size: the number of items per page (defaults to 50)
            sort: the video field to sort by (defaults to "date_added")
            direction: the sort direction (defaults to "descending")
    """
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_access(request.user, course_key):
        raise PermissionDenied()

    response_format = request.REQUEST.get('format', 'html')
    if request.method == 'GET':  # assume html
        return _videos_index(request, course_key)
    else:
        return HttpResponseNotFound()


def _videos_index(request, course_key):
    """
    Display an editable asset library.

    Supports start (0-based index into the list of assets) and max query parameters.
    """
    course_module = modulestore().get_course(course_key)

    return render_to_response('videos_index.html', {
        'context_course': course_module
    })
