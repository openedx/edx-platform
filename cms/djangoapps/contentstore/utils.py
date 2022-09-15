"""
Common utility functions useful throughout the contentstore
"""

import logging
from contextlib import contextmanager
from datetime import datetime

from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocator
from pytz import UTC

from cms.djangoapps.contentstore.toggles import exam_setting_view_enabled
from common.djangoapps.student import auth
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from openedx.core.djangoapps.course_apps.toggles import proctoring_settings_modal_view_enabled
from openedx.core.djangoapps.discussions.config.waffle import ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND
from openedx.core.djangoapps.django_comment_common.models import assign_default_role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.content_type_gating.partitions import CONTENT_TYPE_GATING_SCHEME
from cms.djangoapps.contentstore.toggles import use_new_text_editor, use_new_video_editor
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.partitions.partitions_service import get_all_partitions_for_course  # lint-amnesty, pylint: disable=wrong-import-order

log = logging.getLogger(__name__)


def add_instructor(course_key, requesting_user, new_instructor):
    """
    Adds given user as instructor and staff to the given course,
    after verifying that the requesting_user has permission to do so.
    """
    # can't use auth.add_users here b/c it requires user to already have Instructor perms in this course
    CourseInstructorRole(course_key).add_users(new_instructor)
    auth.add_users(requesting_user, CourseStaffRole(course_key), new_instructor)


def initialize_permissions(course_key, user_who_created_course):
    """
    Initializes a new course by enrolling the course creator as a student,
    and initializing Forum by seeding its permissions and assigning default roles.
    """
    # seed the forums
    seed_permissions_roles(course_key)

    # auto-enroll the course creator in the course so that "View Live" will work.
    CourseEnrollment.enroll(user_who_created_course, course_key)

    # set default forum roles (assign 'Student' role)
    assign_default_role(course_key, user_who_created_course)


def remove_all_instructors(course_key):
    """
    Removes all instructor and staff users from the given course.
    """
    staff_role = CourseStaffRole(course_key)
    staff_role.remove_users(*staff_role.users_with_role())
    instructor_role = CourseInstructorRole(course_key)
    instructor_role.remove_users(*instructor_role.users_with_role())


def delete_course(course_key, user_id, keep_instructors=False):
    """
    Delete course from module store and if specified remove user and
    groups permissions from course.
    """
    _delete_course_from_modulestore(course_key, user_id)

    if not keep_instructors:
        _remove_instructors(course_key)


def _delete_course_from_modulestore(course_key, user_id):
    """
    Delete course from MongoDB. Deleting course will fire a signal which will result into
    deletion of the courseware associated with a course_key.
    """
    module_store = modulestore()

    with module_store.bulk_operations(course_key):
        module_store.delete_course(course_key, user_id)


def _remove_instructors(course_key):
    """
    In the django layer, remove all the user/groups permissions associated with this course
    """
    print('removing User permissions from course....')

    try:
        remove_all_instructors(course_key)
    except Exception as err:  # lint-amnesty, pylint: disable=broad-except
        log.error(f"Error in deleting course groups for {course_key}: {err}")


def get_lms_link_for_item(location, preview=False):
    """
    Returns an LMS link to the course with a jump_to to the provided location.

    :param location: the location to jump to
    :param preview: True if the preview version of LMS should be returned. Default value is false.
    """
    assert isinstance(location, UsageKey)

    # checks LMS_BASE value in site configuration for the given course_org_filter(org)
    # if not found returns settings.LMS_BASE
    lms_base = SiteConfiguration.get_value_for_org(
        location.org,
        "LMS_BASE",
        settings.LMS_BASE
    )

    if lms_base is None:
        return None

    if preview:
        # checks PREVIEW_LMS_BASE value in site configuration for the given course_org_filter(org)
        # if not found returns settings.FEATURES.get('PREVIEW_LMS_BASE')
        lms_base = SiteConfiguration.get_value_for_org(
            location.org,
            "PREVIEW_LMS_BASE",
            settings.FEATURES.get('PREVIEW_LMS_BASE')
        )

    return "//{lms_base}/courses/{course_key}/jump_to/{location}".format(
        lms_base=lms_base,
        course_key=str(location.course_key),
        location=str(location),
    )


def get_lms_link_for_certificate_web_view(course_key, mode):
    """
    Returns the url to the certificate web view.
    """
    assert isinstance(course_key, CourseKey)

    # checks LMS_BASE value in SiteConfiguration against course_org_filter if not found returns settings.LMS_BASE
    lms_base = SiteConfiguration.get_value_for_org(course_key.org, "LMS_BASE", settings.LMS_BASE)

    if lms_base is None:
        return None

    return "//{certificate_web_base}/certificates/course/{course_id}?preview={mode}".format(
        certificate_web_base=lms_base,
        course_id=str(course_key),
        mode=mode
    )


def get_course_authoring_url(course_locator):
    """
    Gets course authoring microfrontend URL
    """
    return configuration_helpers.get_value_for_org(
        course_locator.org,
        'COURSE_AUTHORING_MICROFRONTEND_URL',
        settings.COURSE_AUTHORING_MICROFRONTEND_URL
    )


def get_pages_and_resources_url(course_locator):
    """
    Gets course authoring microfrontend URL for Pages and Resources view.
    """
    pages_and_resources_url = None
    if ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND.is_enabled(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        if mfe_base_url:
            pages_and_resources_url = f'{mfe_base_url}/course/{course_locator}/pages-and-resources'
    return pages_and_resources_url


def get_proctored_exam_settings_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for links to proctored exam settings page
    """
    proctored_exam_settings_url = ''
    if exam_setting_view_enabled():
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}'
        if mfe_base_url:
            if proctoring_settings_modal_view_enabled(course_locator):
                proctored_exam_settings_url = f'{course_mfe_url}/pages-and-resources/proctoring/settings'
            else:
                proctored_exam_settings_url = f'{course_mfe_url}/proctored-exam-settings'
    return proctored_exam_settings_url


def get_editor_page_base_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for links to the new base editors
    """
    editor_url = None
    if use_new_text_editor() or use_new_video_editor():
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/editor'
        if mfe_base_url:
            editor_url = course_mfe_url
    return editor_url


def course_import_olx_validation_is_enabled():
    """
    Check if course olx validation is enabled on course import.
    """
    return settings.FEATURES.get('ENABLE_COURSE_OLX_VALIDATION', False)


# pylint: disable=invalid-name
def is_currently_visible_to_students(xblock):
    """
    Returns true if there is a published version of the xblock that is currently visible to students.
    This means that it has a release date in the past, and the xblock has not been set to staff only.
    """

    try:
        published = modulestore().get_item(xblock.location, revision=ModuleStoreEnum.RevisionOption.published_only)
    # If there's no published version then the xblock is clearly not visible
    except ItemNotFoundError:
        return False

    # If visible_to_staff_only is True, this xblock is not visible to students regardless of start date.
    if published.visible_to_staff_only:
        return False

    # Check start date
    if 'detached' not in published._class_tags and published.start is not None:  # lint-amnesty, pylint: disable=protected-access
        return datetime.now(UTC) > published.start

    # No start date, so it's always visible
    return True


def has_children_visible_to_specific_partition_groups(xblock):
    """
    Returns True if this xblock has children that are limited to specific user partition groups.
    Note that this method is not recursive (it does not check grandchildren).
    """
    if not xblock.has_children:
        return False

    for child in xblock.get_children():
        if is_visible_to_specific_partition_groups(child):
            return True

    return False


def is_visible_to_specific_partition_groups(xblock):
    """
    Returns True if this xblock has visibility limited to specific user partition groups.
    """
    if not xblock.group_access:
        return False

    for partition in get_user_partition_info(xblock):
        if any(g["selected"] for g in partition["groups"]):
            return True

    return False


def find_release_date_source(xblock):
    """
    Finds the ancestor of xblock that set its release date.
    """

    # Stop searching at the section level
    if xblock.category == 'chapter':
        return xblock

    parent_location = modulestore().get_parent_location(xblock.location,
                                                        revision=ModuleStoreEnum.RevisionOption.draft_preferred)
    # Orphaned xblocks set their own release date
    if not parent_location:
        return xblock

    parent = modulestore().get_item(parent_location)
    if parent.start != xblock.start:
        return xblock
    else:
        return find_release_date_source(parent)


def find_staff_lock_source(xblock):
    """
    Returns the xblock responsible for setting this xblock's staff lock, or None if the xblock is not staff locked.
    If this xblock is explicitly locked, return it, otherwise find the ancestor which sets this xblock's staff lock.
    """

    # Stop searching if this xblock has explicitly set its own staff lock
    if xblock.fields['visible_to_staff_only'].is_set_on(xblock):
        return xblock

    # Stop searching at the section level
    if xblock.category == 'chapter':
        return None

    parent_location = modulestore().get_parent_location(xblock.location,
                                                        revision=ModuleStoreEnum.RevisionOption.draft_preferred)
    # Orphaned xblocks set their own staff lock
    if not parent_location:
        return None

    parent = modulestore().get_item(parent_location)
    return find_staff_lock_source(parent)


def ancestor_has_staff_lock(xblock, parent_xblock=None):
    """
    Returns True iff one of xblock's ancestors has staff lock.
    Can avoid mongo query by passing in parent_xblock.
    """
    if parent_xblock is None:
        parent_location = modulestore().get_parent_location(xblock.location,
                                                            revision=ModuleStoreEnum.RevisionOption.draft_preferred)
        if not parent_location:
            return False
        parent_xblock = modulestore().get_item(parent_location)
    return parent_xblock.visible_to_staff_only


def reverse_url(handler_name, key_name=None, key_value=None, kwargs=None):
    """
    Creates the URL for the given handler.
    The optional key_name and key_value are passed in as kwargs to the handler.
    """
    kwargs_for_reverse = {key_name: str(key_value)} if key_name else None
    if kwargs:
        kwargs_for_reverse.update(kwargs)
    return reverse(handler_name, kwargs=kwargs_for_reverse)


def reverse_course_url(handler_name, course_key, kwargs=None):
    """
    Creates the URL for handlers that use course_keys as URL parameters.
    """
    return reverse_url(handler_name, 'course_key_string', course_key, kwargs)


def reverse_library_url(handler_name, library_key, kwargs=None):
    """
    Creates the URL for handlers that use library_keys as URL parameters.
    """
    return reverse_url(handler_name, 'library_key_string', library_key, kwargs)


def reverse_usage_url(handler_name, usage_key, kwargs=None):
    """
    Creates the URL for handlers that use usage_keys as URL parameters.
    """
    return reverse_url(handler_name, 'usage_key_string', usage_key, kwargs)


def get_split_group_display_name(xblock, course):
    """
    Returns group name if an xblock is found in user partition groups that are suitable for the split_test module.

    Arguments:
        xblock (XBlock): The courseware component.
        course (XBlock): The course descriptor.

    Returns:
        group name (String): Group name of the matching group xblock.
    """
    for user_partition in get_user_partition_info(xblock, schemes=['random'], course=course):
        for group in user_partition['groups']:
            if 'Group ID {group_id}'.format(group_id=group['id']) == xblock.display_name_with_default:
                return group['name']


def get_user_partition_info(xblock, schemes=None, course=None):
    """
    Retrieve user partition information for an XBlock for display in editors.

    * If a partition has been disabled, it will be excluded from the results.

    * If a group within a partition is referenced by the XBlock, but the group has been deleted,
      the group will be marked as deleted in the results.

    Arguments:
        xblock (XBlock): The courseware component being edited.

    Keyword Arguments:
        schemes (iterable of str): If provided, filter partitions to include only
            schemes with the provided names.

        course (XBlock): The course descriptor.  If provided, uses this to look up the user partitions
            instead of loading the course.  This is useful if we're calling this function multiple
            times for the same course want to minimize queries to the modulestore.

    Returns: list

    Example Usage:
    >>> get_user_partition_info(block, schemes=["cohort", "verification"])
    [
        {
            "id": 12345,
            "name": "Cohorts"
            "scheme": "cohort",
            "groups": [
                {
                    "id": 7890,
                    "name": "Foo",
                    "selected": True,
                    "deleted": False,
                }
            ]
        },
        {
            "id": 7292,
            "name": "Midterm A",
            "scheme": "verification",
            "groups": [
                {
                    "id": 1,
                    "name": "Completed verification at Midterm A",
                    "selected": False,
                    "deleted": False
                },
                {
                    "id": 0,
                    "name": "Did not complete verification at Midterm A",
                    "selected": False,
                    "deleted": False,
                }
            ]
        }
    ]

    """
    course = course or modulestore().get_course(xblock.location.course_key)

    if course is None:
        log.warning(
            "Could not find course %s to retrieve user partition information",
            xblock.location.course_key
        )
        return []

    if schemes is not None:
        schemes = set(schemes)

    partitions = []
    for p in sorted(get_all_partitions_for_course(course, active_only=True), key=lambda p: p.name):

        # Exclude disabled partitions, partitions with no groups defined
        # The exception to this case is when there is a selected group within that partition, which means there is
        # a deleted group
        # Also filter by scheme name if there's a filter defined.
        selected_groups = set(xblock.group_access.get(p.id, []) or [])
        if (p.groups or selected_groups) and (schemes is None or p.scheme.name in schemes):

            # First, add groups defined by the partition
            groups = []
            for g in p.groups:
                # Falsey group access for a partition mean that all groups
                # are selected.  In the UI, though, we don't show the particular
                # groups selected, since there's a separate option for "all users".
                groups.append({
                    "id": g.id,
                    "name": g.name,
                    "selected": g.id in selected_groups,
                    "deleted": False,
                })

            # Next, add any groups set on the XBlock that have been deleted
            all_groups = {g.id for g in p.groups}
            missing_group_ids = selected_groups - all_groups
            for gid in missing_group_ids:
                groups.append({
                    "id": gid,
                    "name": _("Deleted Group"),
                    "selected": True,
                    "deleted": True,
                })

            # Put together the entire partition dictionary
            partitions.append({
                "id": p.id,
                "name": str(p.name),  # Convert into a string in case ugettext_lazy was used
                "scheme": p.scheme.name,
                "groups": groups,
            })

    return partitions


def get_visibility_partition_info(xblock, course=None):
    """
    Retrieve user partition information for the component visibility editor.

    This pre-processes partition information to simplify the template.

    Arguments:
        xblock (XBlock): The component being edited.

        course (XBlock): The course descriptor.  If provided, uses this to look up the user partitions
            instead of loading the course.  This is useful if we're calling this function multiple
            times for the same course want to minimize queries to the modulestore.

    Returns: dict

    """
    selectable_partitions = []
    # We wish to display enrollment partitions before cohort partitions.
    enrollment_user_partitions = get_user_partition_info(xblock, schemes=["enrollment_track"], course=course)

    # For enrollment partitions, we only show them if there is a selected group or
    # or if the number of groups > 1.
    for partition in enrollment_user_partitions:
        if len(partition["groups"]) > 1 or any(group["selected"] for group in partition["groups"]):
            selectable_partitions.append(partition)

    course_key = xblock.scope_ids.usage_id.course_key
    is_library = isinstance(course_key, LibraryLocator)
    if not is_library and ContentTypeGatingConfig.current(course_key=course_key).studio_override_enabled:
        selectable_partitions += get_user_partition_info(xblock, schemes=[CONTENT_TYPE_GATING_SCHEME], course=course)

    # Now add the cohort user partitions.
    selectable_partitions = selectable_partitions + get_user_partition_info(xblock, schemes=["cohort"], course=course)

    # Find the first partition with a selected group. That will be the one initially enabled in the dialog
    # (if the course has only been added in Studio, only one partition should have a selected group).
    selected_partition_index = -1

    # At the same time, build up all the selected groups as they are displayed in the dialog title.
    selected_groups_label = ''

    for index, partition in enumerate(selectable_partitions):
        for group in partition["groups"]:
            if group["selected"]:
                if len(selected_groups_label) == 0:
                    selected_groups_label = group['name']
                else:
                    # Translators: This is building up a list of groups. It is marked for translation because of the
                    # comma, which is used as a separator between each group.
                    selected_groups_label = _('{previous_groups}, {current_group}').format(
                        previous_groups=selected_groups_label,
                        current_group=group['name']
                    )
                if selected_partition_index == -1:
                    selected_partition_index = index

    return {
        "selectable_partitions": selectable_partitions,
        "selected_partition_index": selected_partition_index,
        "selected_groups_label": selected_groups_label,
    }


def get_xblock_aside_instance(usage_key):
    """
    Returns: aside instance of a aside xblock
    :param usage_key: Usage key of aside xblock
    """
    try:
        descriptor = modulestore().get_item(usage_key.usage_key)
        for aside in descriptor.runtime.get_asides(descriptor):
            if aside.scope_ids.block_type == usage_key.aside_type:
                return aside
    except ItemNotFoundError:
        log.warning('Unable to load item %s', usage_key.usage_key)


def is_self_paced(course):
    """
    Returns True if course is self-paced, False otherwise.
    """
    return course and course.self_paced


def get_sibling_urls(subsection, unit_location):    # pylint: disable=too-many-statements
    """
    Given a subsection, returns the urls for the next and previous units.

    (the first unit of the next subsection or section, and
    the last unit of the previous subsection/section)
    """
    def get_unit_location(direction):
        """
        Returns the desired location of the adjacent unit in a subsection.
        """
        unit_index = subsection.children.index(unit_location)
        try:
            if direction == 'previous':
                if unit_index > 0:
                    location = subsection.children[unit_index - 1]
                else:
                    location = None
            else:
                location = subsection.children[unit_index + 1]
            return location
        except IndexError:
            return None

    def get_subsections_in_section():
        """
        Returns subsections present in a section.
        """
        try:
            section_subsections = section.get_children()
            return section_subsections
        except AttributeError:
            log.error("URL Retrieval Error: subsection {subsection} included in section {section}".format(
                section=section.location,
                subsection=subsection.location
            ))
            return None

    def get_sections_in_course():
        """
        Returns sections present in course.
        """
        try:
            section_subsections = section.get_parent().get_children()
            return section_subsections
        except AttributeError:
            log.error("URL Retrieval Error: In section {section} in course".format(
                section=section.location,
            ))
            return None

    def get_subsection_location(section_subsections, current_subsection, direction):
        """
        Returns the desired location of the adjacent subsections in a section.
        """
        location = None
        subsection_index = section_subsections.index(next(s for s in subsections if s.location ==
                                                          current_subsection.location))
        try:
            if direction == 'previous':
                if subsection_index > 0:
                    prev_subsection = subsections[subsection_index - 1]
                    location = prev_subsection.get_children()[-1].location
            else:
                next_subsection = subsections[subsection_index + 1]
                location = next_subsection.get_children()[0].location
            return location
        except IndexError:
            return None

    def get_section_location(course_sections, current_section, direction):
        """
        Returns the desired location of the adjacent sections in a course.
        """
        location = None
        section_index = course_sections.index(next(s for s in sections if s.location == current_section.location))
        try:
            if direction == 'previous':
                if section_index > 0:
                    prev_section = sections[section_index - 1]
                    location = prev_section.get_children()[-1].get_children()[-1].location
            else:
                next_section = sections[section_index + 1]
                location = next_section.get_children()[0].get_children()[0].location
            return location
        except IndexError:
            return None

    section = subsection.get_parent()
    prev_url = next_url = ''

    prev_loc = get_unit_location('previous')
    next_loc = get_unit_location('next')

    if not prev_loc:
        subsections = get_subsections_in_section()
        if subsections:
            prev_loc = get_subsection_location(subsections, subsection, 'previous')

    if not next_loc:
        subsections = get_subsections_in_section()
        if subsections:
            next_loc = get_subsection_location(subsections, subsection, 'next')

    if not prev_loc:
        sections = get_sections_in_course()
        if sections:
            prev_loc = get_section_location(sections, section, 'previous')

    if not next_loc:
        sections = get_sections_in_course()
        if sections:
            next_loc = get_section_location(sections, section, 'next')

    if prev_loc:
        prev_url = reverse_usage_url('container_handler', prev_loc)
    if next_loc:
        next_url = reverse_usage_url('container_handler', next_loc)
    return prev_url, next_url


def determine_label(display_name, block_type):
    """
    Returns the name of the xblock to display in studio.
    Please see TNL-9838.
    """
    if display_name in {"", None}:
        if block_type == 'html':
            return _("Text")
        else:
            return block_type
    else:
        return display_name


@contextmanager
def translation_language(language):
    """Context manager to override the translation language for the scope
    of the following block. Has no effect if language is None.
    """
    if language:
        previous = translation.get_language()
        translation.activate(language)
        try:
            yield
        finally:
            translation.activate(previous)
    else:
        yield
