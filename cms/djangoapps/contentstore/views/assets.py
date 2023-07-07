"""Views for assets"""


import json
import logging
import math
import re
from functools import partial
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpResponseNotFound
from django.utils.translation import gettext as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST
from cms.djangoapps.contentstore.asset_storage_handlers import (
    handle_assets,
    update_course_run_asset as update_course_run_asset_source_method,
    get_file_size as get_file_size_source_method,
    delete_asset as delete_asset_source_method,
    get_asset_json as get_asset_json_source_method,
    update_asset as update_asset_source_method,
)
from opaque_keys.edx.keys import AssetKey, CourseKey
from pymongo import ASCENDING, DESCENDING

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.date_utils import get_default_time_display
from common.djangoapps.util.json_request import JsonResponse
from openedx.core.djangoapps.contentserver.caching import del_cached_content
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xmodule.contentstore.content import StaticContent  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.contentstore.django import contentstore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.exceptions import NotFoundError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order

from ..exceptions import AssetNotFoundException, AssetSizeTooLargeException
from ..utils import reverse_course_url

__all__ = ['assets_handler']

REQUEST_DEFAULTS = {
    'page': 0,
    'page_size': 50,
    'sort': 'date_added',
    'direction': '',
    'asset_type': '',
    'text_search': '',
}


@login_required
@ensure_csrf_cookie
def assets_handler(request, course_key_string=None, asset_key_string=None):
    '''
    The restful handler for assets.
    It allows retrieval of all the assets (as an HTML page), as well as uploading new assets,
    deleting assets, and changing the 'locked' state of an asset.

    GET
        html: return an html page which will show all course assets. Note that only the asset container
            is returned and that the actual assets are filled in with a client-side request.
        json: returns a page of assets. The following parameters are supported:
            page: the desired page of results (defaults to 0)
            page_size: the number of items per page (defaults to 50)
            sort: the asset field to sort by (defaults to 'date_added')
            direction: the sort direction (defaults to 'descending')
            asset_type: the file type to filter items to (defaults to All)
            text_search: string to filter results by file name (defaults to '')
    POST
        json: create (or update?) an asset. The only updating that can be done is changing the lock state.
    PUT
        json: update the locked state of an asset
    DELETE
        json: delete an asset
    '''
    return handle_assets(request, course_key_string, asset_key_string)


def update_course_run_asset(course_key, upload_file):
    """Exposes service method in asset_storage_handlers without breaking existing bindings/dependencies"""
    return update_course_run_asset_source_method(course_key, upload_file)


def get_file_size(upload_file):
    """Exposes service method in asset_storage_handlers without breaking existing bindings/dependencies"""
    return get_file_size_source_method(upload_file)


def delete_asset(course_key, asset_key):
    """Exposes service method in asset_storage_handlers without breaking existing bindings/dependencies"""
    return delete_asset_source_method(course_key, asset_key)

def _get_asset_json(display_name, content_type, date, location, thumbnail_location, locked, course_key):
    return get_asset_json_source_method(
        display_name,
        content_type,
        date,
        location,
        thumbnail_location,
        locked,
        course_key,
    )

def _update_asset(request, course_key, asset_key):
    return update_asset_source_method(request, course_key, asset_key)
