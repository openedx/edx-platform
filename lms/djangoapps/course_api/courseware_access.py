""" Centralized access to LMS courseware app """

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware import courses, module_render
from courseware.model_data import FieldDataCache


def get_course(course_id, depth=0):
    """
    Utility method to obtain course components
    """
    course_descriptor = None
    course_content = None
    course_key = CourseKey.from_string(course_id)
    if course_key:
        course_descriptor = get_course_descriptor(course_key, depth)
    return course_descriptor, course_key, course_content


def get_course_child(request, user, course_key, content_id, depth=None):
    """
    Return a course xmodule/xblock to the caller
    """
    child_descriptor = None
    child_content = None
    child_key = get_course_child_key(content_id)
    if child_key:
        try:
            child_descriptor = modulestore().get_item(child_key, depth=depth)
        except ItemNotFoundError:
            child_descriptor = None

        if child_descriptor:
            child_content = get_course_content(request, user, course_key, child_descriptor)
    return child_descriptor, child_key, child_content


def get_course_descriptor(course_key, depth):
    """
    Utility method to abstract away the work of loading a course descriptor
    """
    try:
        return courses.get_course(course_key, depth)
    except ValueError:
        return None


def get_course_content(request, user, course_key, course_descriptor):
    """
    Utility method to abstract away the work of loading a course content module/object
    """
    field_data_cache = FieldDataCache([course_descriptor], course_key, user)
    course_content = module_render.get_module_for_descriptor(
        user,
        request,
        course_descriptor,
        field_data_cache,
        course_key)
    return course_content


def get_course_child_key(content_id):
    """
    Utility method to generate a Location/Usage key for the specified course content identifier
    """
    try:
        content_key = UsageKey.from_string(content_id)
    except InvalidKeyError:
        content_key = None

    return content_key
