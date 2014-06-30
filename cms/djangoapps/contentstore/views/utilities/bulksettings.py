"""
Views related to bulk settings change operations on course objects.
"""

import logging

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from edxmako.shortcuts import render_to_response

from contentstore.utils import BulkSettingsUtil

from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from ..access import has_course_access

log = logging.getLogger(__name__)

__all__ = ['utility_bulksettings_handler']

COMPONENT_TYPES = ['discussion', 'html', 'problem', 'video']

SECTION_SETTING_MAP = {'start': 'Release Date'}
SUBSECTION_SETTING_MAP = {'start': 'Release', 'due': 'Due', 'format': 'Type'}
CATEGORY_SETTING_MAP = BulkSettingsUtil.CATEGORY_SETTING_MAP
SETTING_TYPE_LIST_MAP = {
    "section_setting_types": BulkSettingsUtil.SECTION_SETTING_TYPES,
    "subsection_setting_types": BulkSettingsUtil.SUBSECTION_SETTING_TYPES,
    "unit_setting_types": BulkSettingsUtil.UNIT_SETTING_TYPES,
    "problem_setting_types": BulkSettingsUtil.PROBLEM_SETTING_TYPES
}


@login_required
def utility_bulksettings_handler(request, course_key_string):
    """
    Handler for bulk settings view requests in the utilities tool.
    Queries for all settings for a given section, subsection & xblocks.

    In order to reduce the amount of embedding of functions in the template,
    store section - subsection - units - problems as list of hashes
    """

    course_key = CourseKey.from_string(course_key_string)
    response_format = request.REQUEST.get('format', 'html')

    if response_format == 'html':
        if request.method == 'GET':

            # load data
            course = _get_course_module(course_key, request.user, depth=3)

            # traverse into the course tree and extract problem settings information
            settings_data = BulkSettingsUtil.get_bulksettings_metadata(course)
            return render_to_response('bulksettings.html',
                {
                    'context_course':course,
                    'settings_data':settings_data,
                    'setting_type_list_map': SETTING_TYPE_LIST_MAP,
                    'section_setting_map': SECTION_SETTING_MAP,
                    'subsection_setting_map': SUBSECTION_SETTING_MAP
                }
            )


def _get_course_module(course_key, user, depth=0):
    """
    return the course module for the view functions.
    Safety-check if the given user has permissions to access the course module.
    """

    if not has_course_access(user, course_key):
        raise PermissionDenied()
    course_module = modulestore().get_course(course_key, depth = depth)
    return course_module

