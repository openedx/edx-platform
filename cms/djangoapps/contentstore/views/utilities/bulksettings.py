"""
Views related to bulk settings change operations on course objects.
"""

import logging
from datetime import datetime

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required

from edxmako.shortcuts import render_to_response

from contentstore.views.helpers import xblock_studio_url
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from student.auth import has_course_author_access
from ..course import get_course_and_check_access


class BulkSettingsUtil():
    """
    Utility class that hold functions for bulksettings operations
    """

    COMPONENT_TYPES = ['discussion', 'html', 'problem', 'video']

    SECTION_SETTING_TYPES = ['start']
    SUBSECTION_SETTING_TYPES = ['start', 'due', 'format']
    UNIT_SETTING_TYPES = []
    PROBLEM_SETTING_TYPES = ['max_attempts', 'weight', 'rerandomize', 'showanswer', 'submission_wait_seconds']
    SECTION_SETTING_MAP = {'start': 'Release Date'}
    SUBSECTION_SETTING_MAP = {'start': 'Release', 'due': 'Due', 'format': 'Type'}
    CATEGORY_SETTING_MAP = {
        "chapter": SECTION_SETTING_TYPES,
        "sequential": SUBSECTION_SETTING_TYPES,
        "vertical": UNIT_SETTING_TYPES,
        "problem": PROBLEM_SETTING_TYPES,
    }

    @classmethod
    def get_settings_dict_for_category(cls, category, child, parent):
        """
        Returns the settings dictionary for the given child of given category.
        Parent is required since .parent nor .get_parent() work.
        """

        settings_dict = {}
        settings_dict['name'] = child.display_name
        settings_dict['children'] = []
        settings_dict['url'] = cls.get_settings_url_for_category(category, child, parent)

        for setting_type in cls.CATEGORY_SETTING_MAP[category]:
            value = getattr(child, setting_type)
            if isinstance(value, datetime):
                value = value.strftime('%m/%d/%Y')

            settings_dict[setting_type] = value

        if category == 'vertical':
            settings_dict['ispublic'] = modulestore().has_published_version(child)

        return settings_dict

    @classmethod
    def get_settings_url_for_category(cls, category, child, parent):
        """
        Returns the URLs that the user needs to go to in order to change settings.
        Chapters and Problems need urls that match for their parents:
            - Chapters: Course url
            - Problems: Unit url
        """

        if category in ['chapter', 'sequential', 'vertical']:
            return xblock_studio_url(child)
        else:
            return xblock_studio_url(parent)

    @classmethod
    def get_bulksettings_metadata(cls, course):
        """
        Returns a list of settings metadata for all sections, subsections, units, and problems.
        Each block (section, subsection, unit or problem) settings metadata is saved as a dictionary:
            settings_data =  {
                'name' = name of the block
                'key' = opaquekey. Used for link generation
                'children' = List of children_settings_data
            }
        """

        settings_data = []

        for section in course.get_children():
            section_setting = cls.get_settings_dict_for_category('chapter', section, course)

            for subsection in section.get_children():
                subsection_setting = cls.get_settings_dict_for_category('sequential', subsection, section)

                for unit in subsection.get_children():
                    unit_setting = cls.get_settings_dict_for_category('vertical', unit, subsection)

                    for component in unit.get_children():

                        if component.location.category == 'problem':
                            curr_problem_settings = cls.get_settings_dict_for_category('problem', component, unit)
                            unit_setting['children'].append(curr_problem_settings)

                    if unit_setting['children']:
                        subsection_setting['children'].append(unit_setting)
                if subsection_setting['children']:
                    section_setting['children'].append(subsection_setting)
            if section_setting['children']:
                settings_data.append(section_setting)

        return settings_data


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
            course = get_course_and_check_access(course_key, request.user, depth=3)

            # traverse into the course tree and extract problem settings information
            settings_data = BulkSettingsUtil.get_bulksettings_metadata(course)
            return render_to_response(
                'bulksettings.html',
                {
                    'context_course': course,
                    'settings_data': settings_data,
                    'setting_type_list_map': SETTING_TYPE_LIST_MAP,
                    'section_setting_map': SECTION_SETTING_MAP,
                    'subsection_setting_map': SUBSECTION_SETTING_MAP
                }
            )
