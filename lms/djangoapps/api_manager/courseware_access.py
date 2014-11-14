""" Centralized access to LMS courseware app """
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django.conf import settings

from courseware import courses, module_render
from courseware.model_data import FieldDataCache
from student.roles import CourseRole, CourseObserverRole
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from xmodule.modulestore import InvalidLocationError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


def _anonymous_known_flag(user):
    if isinstance(user, AnonymousUser):
        user.known = False

def get_modulestore():
    return modulestore()


def get_course(request, user, course_id, depth=0, load_content=False):
    """
    Utility method to obtain course components
    """
    _anonymous_known_flag(user)
    course_descriptor = None
    course_content = None
    course_key = get_course_key(course_id)
    if course_key:
        course_descriptor = get_course_descriptor(course_key, depth)
        if course_descriptor and load_content:
            course_content = get_course_content(request, user, course_key, course_descriptor)
    return course_descriptor, course_key, course_content


def get_course_child(request, user, course_key, content_id, load_content=False):
    """
    Return a course xmodule/xblock to the caller
    """
    _anonymous_known_flag(user)
    child_descriptor = None
    child_content = None
    child_key = get_course_child_key(content_id)
    if child_key:
        child_descriptor = get_course_child_descriptor(child_key)
        if child_descriptor and load_content:
            child_content = get_course_child_content(request, user, course_key, child_descriptor)
    return child_descriptor, child_key, child_content


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


def get_course_leaf_nodes(course_key):
    """
    Get count of the leaf nodes with ability to exclude some categories
    """
    nodes = []
    detached_categories = getattr(settings, 'PROGRESS_DETACHED_CATEGORIES', [])
    store = get_modulestore()
    verticals = store.get_items(course_key,  qualifiers={'category': 'vertical'})
    orphans = store.get_orphans(course_key)
    for vertical in verticals:
        if hasattr(vertical, 'children') and vertical.location not in orphans:
            nodes.extend([unit for unit in vertical.children
                          if getattr(unit, 'category') not in detached_categories])
    return nodes


def get_course_key(course_id, slashseparated=False):
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            course_key = None
    if slashseparated:
        try:
            course_key = course_key.to_deprecated_string()
        except:
            course_key = course_id
    return course_key


def get_course_descriptor(course_key, depth):
    try:
        course_descriptor = courses.get_course(course_key, depth)
    except ValueError:
        course_descriptor = None
    return course_descriptor


def get_course_content(request, user, course_key, course_descriptor):
    field_data_cache = FieldDataCache([course_descriptor], course_key, user)
    course_content = module_render.get_module_for_descriptor(
        user,
        request,
        course_descriptor,
        field_data_cache,
        course_key)
    return course_content


def course_exists(request, user, course_id):
    course_key = get_course_key(course_id)
    if not course_key:
        return False
    if not get_modulestore().has_course(course_key):
        return False
    return True


def get_course_child_key(content_id):
    try:
        content_key = UsageKey.from_string(content_id)
    except InvalidKeyError:
        try:
            content_key = Location.from_deprecated_string(content_id)
        except (InvalidLocationError, InvalidKeyError):
            content_key = None
    return content_key


def get_course_child_descriptor(child_key):
    try:
        content_descriptor = get_modulestore().get_item(child_key)
    except ItemNotFoundError:
        content_descriptor = None
    return content_descriptor


def get_course_child_content(request, user, course_key, child_descriptor):
    field_data_cache = FieldDataCache([child_descriptor], course_key, user)
    child_content = module_render.get_module_for_descriptor(
        user,
        request,
        child_descriptor,
        field_data_cache,
        course_key)
    return child_content


def get_aggregate_exclusion_user_ids(course_key):
    """
    This helper method will return the list of user ids that are marked in roles
    that can be excluded from certain aggregate queries. The list of roles to exclude
    can be defined in a AGGREGATION_EXCLUDE_ROLES settings variable
    """

    exclude_user_ids = set()
    exclude_role_list = getattr(settings, 'AGGREGATION_EXCLUDE_ROLES', [CourseObserverRole.ROLE])

    for role in exclude_role_list:
        users = CourseRole(role, course_key).users_with_role()
        user_ids = set()
        for user in users:
            user_ids.add(user.id)

        exclude_user_ids = exclude_user_ids.union(user_ids)

    return exclude_user_ids
