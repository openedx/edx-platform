"""
Helper methods for Studio views.
"""

import urllib
from uuid import uuid4

from django.http import HttpResponse
from django.utils.translation import gettext as _
from opaque_keys.edx.keys import UsageKey
from xblock.core import XBlock
from xmodule.modulestore.django import modulestore
from xmodule.tabs import StaticTab

from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseCreatorRole, OrgContentCreatorRole
from openedx.core.toggles import ENTRANCE_EXAMS

from ..utils import reverse_course_url, reverse_library_url, reverse_usage_url

__all__ = ['event']

# Note: Grader types are used throughout the platform but most usages are simply in-line
# strings.  In addition, new grader types can be defined on the fly anytime one is needed
# (because they're just strings). This dict is an attempt to constrain the sprawl in Studio.
GRADER_TYPES = {
    "HOMEWORK": "Homework",
    "LAB": "Lab",
    "ENTRANCE_EXAM": "Entrance Exam",
    "MIDTERM_EXAM": "Midterm Exam",
    "FINAL_EXAM": "Final Exam"
}


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)


def get_parent_xblock(xblock):
    """
    Returns the xblock that is the parent of the specified xblock, or None if it has no parent.
    """
    locator = xblock.location
    parent_location = modulestore().get_parent_location(locator)

    if parent_location is None:
        return None
    return modulestore().get_item(parent_location)


def is_unit(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock is a vertical that is treated as a unit.
    A unit is a vertical that is a direct child of a sequential (aka a subsection).
    """
    if xblock.category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        parent_category = parent_xblock.category if parent_xblock else None
        return parent_category == 'sequential'
    return False


def xblock_has_own_studio_page(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock has an associated Studio page. Most xblocks do
    not have their own page but are instead shown on the page of their parent. There
    are a few exceptions:
      1. Courses
      2. Verticals that are either:
        - themselves treated as units
        - a direct child of a unit
      3. XBlocks that support children
    """
    category = xblock.category

    if is_unit(xblock, parent_xblock):
        return True
    elif category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        return is_unit(parent_xblock) if parent_xblock else False

    # All other xblocks with children have their own page
    return xblock.has_children


def xblock_studio_url(xblock, parent_xblock=None):
    """
    Returns the Studio editing URL for the specified xblock.
    """
    if not xblock_has_own_studio_page(xblock, parent_xblock):
        return None
    category = xblock.category
    if category == 'course':
        return reverse_course_url('course_handler', xblock.location.course_key)
    elif category in ('chapter', 'sequential'):
        return '{url}?show={usage_key}'.format(
            url=reverse_course_url('course_handler', xblock.location.course_key),
            usage_key=urllib.parse.quote(str(xblock.location))
        )
    elif category == 'library':
        library_key = xblock.location.course_key
        return reverse_library_url('library_handler', library_key)
    else:
        return reverse_usage_url('container_handler', xblock.location)


def xblock_type_display_name(xblock, default_display_name=None):
    """
    Returns the display name for the specified type of xblock. Note that an instance can be passed in
    for context dependent names, e.g. a vertical beneath a sequential is a Unit.

    :param xblock: An xblock instance or the type of xblock.
    :param default_display_name: The default value to return if no display name can be found.
    :return:
    """

    if hasattr(xblock, 'category'):
        category = xblock.category
        if category == 'vertical' and not is_unit(xblock):
            return _('Vertical')
    else:
        category = xblock
    if category == 'chapter':
        return _('Section')
    elif category == 'sequential':
        return _('Subsection')
    elif category == 'vertical':
        return _('Unit')
    component_class = XBlock.load_class(category)
    if hasattr(component_class, 'display_name') and component_class.display_name.default:
        return _(component_class.display_name.default)  # lint-amnesty, pylint: disable=translation-of-non-string
    else:
        return default_display_name


def xblock_primary_child_category(xblock):
    """
    Returns the primary child category for the specified xblock, or None if there is not a primary category.
    """
    category = xblock.category
    if category == 'course':
        return 'chapter'
    elif category == 'chapter':
        return 'sequential'
    elif category == 'sequential':
        return 'vertical'
    return None


def usage_key_with_run(usage_key_string):
    """
    Converts usage_key_string to a UsageKey, adding a course run if necessary
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    return usage_key


def remove_entrance_exam_graders(course_key, user):
    """
    Removes existing entrance exam graders attached to the specified course
    Typically used when adding/removing an entrance exam.
    """
    grading_model = CourseGradingModel.fetch(course_key)
    graders = grading_model.graders
    for i, grader in enumerate(graders):
        if grader['type'] == GRADER_TYPES['ENTRANCE_EXAM']:
            CourseGradingModel.delete_grader(course_key, i, user)


def create_xblock(parent_locator, user, category, display_name, boilerplate=None, is_entrance_exam=False):
    """
    Performs the actual grunt work of creating items/xblocks -- knows nothing about requests, views, etc.
    """
    store = modulestore()
    usage_key = usage_key_with_run(parent_locator)
    with store.bulk_operations(usage_key.course_key):
        parent = store.get_item(usage_key)
        dest_usage_key = usage_key.replace(category=category, name=uuid4().hex)

        # get the metadata, display_name, and definition from the caller
        metadata = {}
        data = None
        template_id = boilerplate
        if template_id:
            clz = parent.runtime.load_block_type(category)
            if clz is not None:
                template = clz.get_template(template_id)
                if template is not None:
                    metadata = template.get('metadata', {})
                    data = template.get('data')

        if display_name is not None:
            metadata['display_name'] = display_name

        # We should use the 'fields' kwarg for newer block settings/values (vs. metadata or data)
        fields = {}

        # Entrance Exams: Chapter module positioning
        child_position = None
        if ENTRANCE_EXAMS.is_enabled():
            if category == 'chapter' and is_entrance_exam:
                fields['is_entrance_exam'] = is_entrance_exam
                fields['in_entrance_exam'] = True  # Inherited metadata, all children will have it
                child_position = 0

        # TODO need to fix components that are sending definition_data as strings, instead of as dicts
        # For now, migrate them into dicts here.
        if isinstance(data, str):
            data = {'data': data}

        created_block = store.create_child(
            user.id,
            usage_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            fields=fields,
            definition_data=data,
            metadata=metadata,
            runtime=parent.runtime,
            position=child_position,
        )

        # Entrance Exams: Grader assignment
        if ENTRANCE_EXAMS.is_enabled():
            course_key = usage_key.course_key
            course = store.get_course(course_key)
            if hasattr(course, 'entrance_exam_enabled') and course.entrance_exam_enabled:
                if category == 'sequential' and parent_locator == course.entrance_exam_id:
                    # Clean up any pre-existing entrance exam graders
                    remove_entrance_exam_graders(course_key, user)
                    grader = {
                        "type": GRADER_TYPES['ENTRANCE_EXAM'],
                        "min_count": 0,
                        "drop_count": 0,
                        "short_label": "Entrance",
                        "weight": 0
                    }
                    grading_model = CourseGradingModel.update_grader_from_json(
                        course.id,
                        grader,
                        user
                    )
                    CourseGradingModel.update_section_grader_type(
                        created_block,
                        grading_model['type'],
                        user
                    )

        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course block, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if category == 'static_tab':
            display_name = display_name or _("Empty")  # Prevent name being None
            course = store.get_course(dest_usage_key.course_key)
            course.tabs.append(
                StaticTab(
                    name=display_name,
                    url_slug=dest_usage_key.block_id,
                )
            )
            store.update_item(course, user.id)

        return created_block


def is_item_in_course_tree(item):
    """
    Check that the item is in the course tree.

    It's possible that the item is not in the course tree
    if its parent has been deleted and is now an orphan.
    """
    ancestor = item.get_parent()
    while ancestor is not None and ancestor.location.block_type != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None


def is_content_creator(user, org):
    """
    Check if the user has the role to create content.

    This function checks if the User has role to create content
    or if the org is supplied, it checks for Org level course content
    creator.
    """
    return (auth.user_has_role(user, CourseCreatorRole()) or
            auth.user_has_role(user, OrgContentCreatorRole(org=org)))
