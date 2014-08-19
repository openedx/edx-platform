""" Centralized access to LMS courseware app """

from courseware import courses, module_render
from courseware.model_data import FieldDataCache
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from xmodule.modulestore import InvalidLocationError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def get_course(request, user, course_id, depth=0):
    """
    Utility method to obtain course components
    """
    course_descriptor = None
    course_key = None
    course_content = None
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            pass
    if course_key:
        try:
            course_descriptor = courses.get_course(course_key, depth)
        except ValueError:
            pass
    if course_descriptor:
        field_data_cache = FieldDataCache([course_descriptor], course_key, user)
        course_content = module_render.get_module_for_descriptor(
            user,
            request,
            course_descriptor,
            field_data_cache,
            course_key)
    return course_descriptor, course_key, course_content


def get_course_child(request, user, course_key, content_id):
    """
    Return a course xmodule/xblock to the caller
    """
    content_descriptor = None
    content_key = None
    content = None
    try:
        content_key = UsageKey.from_string(content_id)
    except InvalidKeyError:
        try:
            content_key = Location.from_deprecated_string(content_id)
        except (InvalidLocationError, InvalidKeyError):
            pass
    if content_key:
        try:
            content_descriptor = modulestore().get_item(content_key)
        except ItemNotFoundError:
            pass
        if content_descriptor:
            field_data_cache = FieldDataCache([content_descriptor], course_key, user)
            content = module_render.get_module_for_descriptor(
                user,
                request,
                content_descriptor,
                field_data_cache,
                course_key)
    return content_descriptor, content_key, content


def get_course_total_score(course_summary):
    """
    Traverse course summary to calculate max possible score for a course
    """
    score = 0
    for chapter in course_summary:  # accumulate score of each chapter
        for section in chapter['sections']:
            if section['section_total']:
                score += section['section_total'][1]
    return score


def get_course_leaf_nodes(course_key, detached_categories):
    """
    Get count of the leaf nodes with ability to exclude some categories
    """
    nodes = []
    verticals = modulestore().get_items(course_key, category='vertical')
    for vertical in verticals:
        nodes.extend([unit.location for unit in vertical.get_children()
                      if getattr(unit, 'category') not in detached_categories])
    return nodes
