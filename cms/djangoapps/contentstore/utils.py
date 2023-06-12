"""
Common utility functions useful throughout the contentstore
"""

from collections import defaultdict
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locator import LibraryLocator
from openedx_events.content_authoring.data import DuplicatedXBlockData
from openedx_events.content_authoring.signals import XBLOCK_DUPLICATED
from milestones import api as milestones_api
from pytz import UTC
from xblock.fields import Scope

from cms.djangoapps.contentstore.toggles import exam_setting_view_enabled
from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.edxmako.services import MakoService
from common.djangoapps.student import auth
from common.djangoapps.student.auth import has_studio_read_access, has_studio_write_access
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    GlobalStaff,
)
from common.djangoapps.util.course import get_link_for_about_page
from common.djangoapps.util.milestones_helpers import (
    is_prerequisite_courses_enabled,
    is_valid_course_key,
    remove_prerequisite_course,
    set_prerequisite_courses,
    get_namespace_choices,
    generate_milestone_namespace
)
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from openedx.core import toggles as core_toggles
from openedx.core.djangoapps.course_apps.toggles import proctoring_settings_modal_view_enabled
from openedx.core.djangoapps.credit.api import get_credit_requirements, is_credit_course
from openedx.core.djangoapps.discussions.config.waffle import ENABLE_PAGES_AND_RESOURCES_MICROFRONTEND
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration
from openedx.core.djangoapps.django_comment_common.models import assign_default_role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.courses import course_image_url
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.content_type_gating.partitions import CONTENT_TYPE_GATING_SCHEME
from openedx.features.course_experience.waffle import ENABLE_COURSE_ABOUT_SIDEBAR_HTML
from cms.djangoapps.contentstore.toggles import (
    use_new_advanced_settings_page,
    use_new_course_outline_page,
    use_new_export_page,
    use_new_files_uploads_page,
    use_new_grading_page,
    use_new_course_team_page,
    use_new_home_page,
    use_new_import_page,
    use_new_schedule_details_page,
    use_new_unit_page,
    use_new_updates_page,
    use_new_video_uploads_page,
)
from cms.djangoapps.contentstore.toggles import use_new_text_editor, use_new_video_editor
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.partitions.partitions_service import get_all_partitions_for_course  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.services import SettingsService, ConfigurationService, TeamsConfigurationService


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


def get_studio_home_url():
    """
    Gets course authoring microfrontend URL for Studio Home view.
    """
    studio_home_url = None
    if use_new_home_page():
        mfe_base_url = settings.COURSE_AUTHORING_MICROFRONTEND_URL
        if mfe_base_url:
            studio_home_url = f'{mfe_base_url}/home'
    return studio_home_url


def get_schedule_details_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for schedule and details pages view.
    """
    schedule_details_url = None
    if use_new_schedule_details_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/settings/details'
        if mfe_base_url:
            schedule_details_url = course_mfe_url
    return schedule_details_url


def get_advanced_settings_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for advanced settings page view.
    """
    advanced_settings_url = None
    if use_new_advanced_settings_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/settings/advanced'
        if mfe_base_url:
            advanced_settings_url = course_mfe_url
    return advanced_settings_url


def get_grading_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for grading page view.
    """
    grading_url = None
    if use_new_grading_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/settings/grading'
        if mfe_base_url:
            grading_url = course_mfe_url
    return grading_url


def get_course_team_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for course team page view.
    """
    course_team_url = None
    if use_new_course_team_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/course_team'
        if mfe_base_url:
            course_team_url = course_mfe_url
    return course_team_url


def get_updates_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for updates page view.
    """
    updates_url = None
    if use_new_updates_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/course_info'
        if mfe_base_url:
            updates_url = course_mfe_url
    return updates_url


def get_import_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for import page view.
    """
    import_url = None
    if use_new_import_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/import'
        if mfe_base_url:
            import_url = course_mfe_url
    return import_url


def get_export_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for export page view.
    """
    export_url = None
    if use_new_export_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/export'
        if mfe_base_url:
            export_url = course_mfe_url
    return export_url


def get_files_uploads_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for files and uploads page view.
    """
    files_uploads_url = None
    if use_new_files_uploads_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/assets'
        if mfe_base_url:
            files_uploads_url = course_mfe_url
    return files_uploads_url


def get_video_uploads_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for files and uploads page view.
    """
    video_uploads_url = None
    if use_new_video_uploads_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}/videos/'
        if mfe_base_url:
            video_uploads_url = course_mfe_url
    return video_uploads_url


def get_course_outline_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for course oultine page view.
    """
    course_outline_url = None
    if use_new_course_outline_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/course/{course_locator}'
        if mfe_base_url:
            course_outline_url = course_mfe_url
    return course_outline_url


def get_unit_url(course_locator) -> str:
    """
    Gets course authoring microfrontend URL for unit page view.
    """
    unit_url = None
    if use_new_unit_page(course_locator):
        mfe_base_url = get_course_authoring_url(course_locator)
        course_mfe_url = f'{mfe_base_url}/container/'
        if mfe_base_url:
            unit_url = course_mfe_url
    return unit_url


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
    Returns group name if an xblock is found in user partition groups that are suitable for the split_test block.

    Arguments:
        xblock (XBlock): The courseware component.
        course (XBlock): The course block.

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

        course (XBlock): The course block.  If provided, uses this to look up the user partitions
            instead of loading the course.  This is useful if we're calling this function multiple
            times for the same course want to minimize queries to the modulestore.

    Returns: list

    Example Usage:
    >>> get_user_partition_info(xblock, schemes=["cohort", "verification"])
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

        course (XBlock): The course block.  If provided, uses this to look up the user partitions
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
        xblock = modulestore().get_item(usage_key.usage_key)
        for aside in xblock.runtime.get_asides(xblock):
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


def get_subsections_by_assignment_type(course_key):
    """
    Construct a dictionary mapping each found assignment type in the course
    to a list of dictionaries with the display name of the subsection and
    the display name of the section they are in
    """
    subsections_by_assignment_type = defaultdict(list)

    with modulestore().bulk_operations(course_key):
        course = modulestore().get_course(course_key, depth=3)
        sections = course.get_children()
        for section in sections:
            subsections = section.get_children()
            for subsection in subsections:
                if subsection.format:
                    subsections_by_assignment_type[subsection.format].append(
                        f'{section.display_name} - {subsection.display_name}'
                    )
    return subsections_by_assignment_type


def update_course_discussions_settings(course_key):
    """
    Updates course provider_type when new course is created
    """
    provider = DiscussionsConfiguration.get(context_key=course_key).provider_type
    store = modulestore()
    course = store.get_course(course_key)
    course.discussions_settings['provider_type'] = provider
    store.update_item(course, course.published_by)


def duplicate_block(
    parent_usage_key,
    duplicate_source_usage_key,
    user,
    dest_usage_key=None,
    display_name=None,
    shallow=False,
    is_child=False
):
    """
    Duplicate an existing xblock as a child of the supplied parent_usage_key. You can
    optionally specify what usage key the new duplicate block will use via dest_usage_key.

    If shallow is True, does not copy children. Otherwise, this function calls itself
    recursively, and will set the is_child flag to True when dealing with recursed child
    blocks.
    """
    store = modulestore()
    with store.bulk_operations(duplicate_source_usage_key.course_key):
        source_item = store.get_item(duplicate_source_usage_key)
        if not dest_usage_key:
            # Change the blockID to be unique.
            dest_usage_key = source_item.location.replace(name=uuid4().hex)

        category = dest_usage_key.block_type

        duplicate_metadata, asides_to_create = gather_block_attributes(
            source_item, display_name=display_name, is_child=is_child,
        )

        dest_block = store.create_item(
            user.id,
            dest_usage_key.course_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            definition_data=source_item.get_explicitly_set_fields_by_scope(Scope.content),
            metadata=duplicate_metadata,
            runtime=source_item.runtime,
            asides=asides_to_create
        )

        children_handled = False

        if hasattr(dest_block, 'studio_post_duplicate'):
            # Allow an XBlock to do anything fancy it may need to when duplicated from another block.
            # These blocks may handle their own children or parenting if needed. Let them return booleans to
            # let us know if we need to handle these or not.
            load_services_for_studio(dest_block.runtime, user)
            children_handled = dest_block.studio_post_duplicate(store, source_item)

        # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
        # Because DAGs are not fully supported, we need to actually duplicate each child as well.
        if source_item.has_children and not shallow and not children_handled:
            dest_block.children = dest_block.children or []
            for child in source_item.children:
                dupe = duplicate_block(dest_block.location, child, user=user, is_child=True)
                if dupe not in dest_block.children:  # _duplicate_block may add the child for us.
                    dest_block.children.append(dupe)
            store.update_item(dest_block, user.id)

        # pylint: disable=protected-access
        if 'detached' not in source_item.runtime.load_block_type(category)._class_tags:
            parent = store.get_item(parent_usage_key)
            # If source was already a child of the parent, add duplicate immediately afterward.
            # Otherwise, add child to end.
            if source_item.location in parent.children:
                source_index = parent.children.index(source_item.location)
                parent.children.insert(source_index + 1, dest_block.location)
            else:
                parent.children.append(dest_block.location)
            store.update_item(parent, user.id)

        # .. event_implemented_name: XBLOCK_DUPLICATED
        XBLOCK_DUPLICATED.send_event(
            time=datetime.now(timezone.utc),
            xblock_info=DuplicatedXBlockData(
                usage_key=dest_block.location,
                block_type=dest_block.location.block_type,
                source_usage_key=duplicate_source_usage_key,
            )
        )

        return dest_block.location


def update_from_source(*, source_block, destination_block, user_id):
    """
    Update a block to have all the settings and attributes of another source.

    Copies over all attributes and settings of a source block to a destination
    block. Blocks must be the same type. This function does not modify or duplicate
    children.

    This function is useful when a block, originally copied from a source block, drifts
    and needs to be updated to match the original.

    The modulestore function copy_from_template will copy a block's children recursively,
    replacing the target block's children. It does not, however, update any of the target
    block's settings. copy_from_template, then, is useful for cases like the Library
    Content Block, where the children are the same across all instances, but the settings
    may differ.

    By contrast, for cases where we're copying a block that has drifted from its source,
    we need to update the target block's settings, but we don't want to replace its children,
    or, at least, not only replace its children. update_from_source is useful for these cases.

    This function is meant to be imported by pluggable django apps looking to manage duplicated
    sections of a course. It is placed here for lack of a more appropriate location, since this
    code has not yet been brought up to the standards in OEP-45.
    """
    duplicate_metadata, asides = gather_block_attributes(source_block, display_name=source_block.display_name)
    for key, value in duplicate_metadata.items():
        setattr(destination_block, key, value)
    for key, value in source_block.get_explicitly_set_fields_by_scope(Scope.content).items():
        setattr(destination_block, key, value)
    modulestore().update_item(
        destination_block,
        user_id,
        metadata=duplicate_metadata,
        asides=asides,
    )


def gather_block_attributes(source_item, display_name=None, is_child=False):
    """
    Gather all the attributes of the source block that need to be copied over to a new or updated block.
    """
    # Update the display name to indicate this is a duplicate (unless display name provided).
    # Can't use own_metadata(), b/c it converts data for JSON serialization -
    # not suitable for setting metadata of the new block
    duplicate_metadata = {}
    for field in source_item.fields.values():
        if field.scope == Scope.settings and field.is_set_on(source_item):
            duplicate_metadata[field.name] = field.read_from(source_item)

    if is_child:
        display_name = display_name or source_item.display_name or source_item.category

    if display_name is not None:
        duplicate_metadata['display_name'] = display_name
    else:
        if source_item.display_name is None:
            duplicate_metadata['display_name'] = _("Duplicate of {0}").format(source_item.category)
        else:
            duplicate_metadata['display_name'] = _("Duplicate of '{0}'").format(source_item.display_name)

    asides_to_create = []
    for aside in source_item.runtime.get_asides(source_item):
        for field in aside.fields.values():
            if field.scope in (Scope.settings, Scope.content,) and field.is_set_on(aside):
                asides_to_create.append(aside)
                break

    for aside in asides_to_create:
        for field in aside.fields.values():
            if field.scope not in (Scope.settings, Scope.content,):
                field.delete_from(aside)
    return duplicate_metadata, asides_to_create


def load_services_for_studio(runtime, user):
    """
    Function to set some required services used for XBlock edits and studio_view.
    (i.e. whenever we're not loading _prepare_runtime_for_preview.) This is required to make information
    about the current user (especially permissions) available via services as needed.
    """
    services = {
        "user": DjangoXBlockUserService(user),
        "studio_user_permissions": StudioPermissionsService(user),
        "mako": MakoService(),
        "settings": SettingsService(),
        "lti-configuration": ConfigurationService(CourseAllowPIISharingInLTIFlag),
        "teams_configuration": TeamsConfigurationService(),
        "library_tools": LibraryToolsService(modulestore(), user.id)
    }

    runtime._services.update(services)  # lint-amnesty, pylint: disable=protected-access


def update_course_details(request, course_key, payload, course_block):
    """
    Utils is used to update course details.
    It is used for both DRF and django views.
    """

    from .views.entrance_exam import create_entrance_exam, delete_entrance_exam, update_entrance_exam

    # if pre-requisite course feature is enabled set pre-requisite course
    if is_prerequisite_courses_enabled():
        prerequisite_course_keys = payload.get('pre_requisite_courses', [])
        if prerequisite_course_keys:
            if not all(is_valid_course_key(course_key) for course_key in prerequisite_course_keys):
                raise ValidationError(_("Invalid prerequisite course key"))
            set_prerequisite_courses(course_key, prerequisite_course_keys)
        else:
            # None is chosen, so remove the course prerequisites
            course_milestones = milestones_api.get_course_milestones(
                course_key=course_key,
                relationship="requires",
            )
            for milestone in course_milestones:
                entrance_exam_namespace = generate_milestone_namespace(
                    get_namespace_choices().get('ENTRANCE_EXAM'),
                    course_key
                )
                if milestone["namespace"] != entrance_exam_namespace:
                    remove_prerequisite_course(course_key, milestone)

    # If the entrance exams feature has been enabled, we'll need to check for some
    # feature-specific settings and handle them accordingly
    # We have to be careful that we're only executing the following logic if we actually
    # need to create or delete an entrance exam from the specified course
    if core_toggles.ENTRANCE_EXAMS.is_enabled():
        course_entrance_exam_present = course_block.entrance_exam_enabled
        entrance_exam_enabled = payload.get('entrance_exam_enabled', '') == 'true'
        ee_min_score_pct = payload.get('entrance_exam_minimum_score_pct', None)
        # If the entrance exam box on the settings screen has been checked...
        if entrance_exam_enabled:
            # Load the default minimum score threshold from settings, then try to override it
            entrance_exam_minimum_score_pct = float(settings.ENTRANCE_EXAM_MIN_SCORE_PCT)
            if ee_min_score_pct:
                entrance_exam_minimum_score_pct = float(ee_min_score_pct)
            if entrance_exam_minimum_score_pct.is_integer():
                entrance_exam_minimum_score_pct = entrance_exam_minimum_score_pct / 100
            # If there's already an entrance exam defined, we'll update the existing one
            if course_entrance_exam_present:
                exam_data = {
                    'entrance_exam_minimum_score_pct': entrance_exam_minimum_score_pct
                }
                update_entrance_exam(request, course_key, exam_data)
            # If there's no entrance exam defined, we'll create a new one
            else:
                create_entrance_exam(request, course_key, entrance_exam_minimum_score_pct)

        # If the entrance exam box on the settings screen has been unchecked,
        # and the course has an entrance exam attached...
        elif not entrance_exam_enabled and course_entrance_exam_present:
            delete_entrance_exam(request, course_key)

    # Perform the normal update workflow for the CourseDetails model
    return CourseDetails.update_from_json(course_key, payload, request.user)


def get_course_settings(request, course_key, course_block):
    """
    Utils is used to get context of course settings.
    It is used for both DRF and django views.
    """

    from .views.course import get_courses_accessible_to_user, _process_courses_list

    credit_eligibility_enabled = settings.FEATURES.get('ENABLE_CREDIT_ELIGIBILITY', False)
    upload_asset_url = reverse_course_url('assets_handler', course_key)

    # see if the ORG of this course can be attributed to a defined configuration . In that case, the
    # course about page should be editable in Studio
    publisher_enabled = configuration_helpers.get_value_for_org(
        course_block.location.org,
        'ENABLE_PUBLISHER',
        settings.FEATURES.get('ENABLE_PUBLISHER', False)
    )
    marketing_enabled = configuration_helpers.get_value_for_org(
        course_block.location.org,
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )
    enable_extended_course_details = configuration_helpers.get_value_for_org(
        course_block.location.org,
        'ENABLE_EXTENDED_COURSE_DETAILS',
        settings.FEATURES.get('ENABLE_EXTENDED_COURSE_DETAILS', False)
    )

    about_page_editable = not publisher_enabled
    enrollment_end_editable = GlobalStaff().has_user(request.user) or not publisher_enabled
    short_description_editable = configuration_helpers.get_value_for_org(
        course_block.location.org,
        'EDITABLE_SHORT_DESCRIPTION',
        settings.FEATURES.get('EDITABLE_SHORT_DESCRIPTION', True)
    )
    sidebar_html_enabled = ENABLE_COURSE_ABOUT_SIDEBAR_HTML.is_enabled()

    verified_mode = CourseMode.verified_mode_for_course(course_key, include_expired=True)
    upgrade_deadline = (verified_mode and verified_mode.expiration_datetime and
                        verified_mode.expiration_datetime.isoformat())
    settings_context = {
        'context_course': course_block,
        'course_locator': course_key,
        'lms_link_for_about_page': get_link_for_about_page(course_block),
        'course_image_url': course_image_url(course_block, 'course_image'),
        'banner_image_url': course_image_url(course_block, 'banner_image'),
        'video_thumbnail_image_url': course_image_url(course_block, 'video_thumbnail_image'),
        'details_url': reverse_course_url('settings_handler', course_key),
        'about_page_editable': about_page_editable,
        'marketing_enabled': marketing_enabled,
        'short_description_editable': short_description_editable,
        'sidebar_html_enabled': sidebar_html_enabled,
        'upload_asset_url': upload_asset_url,
        'course_handler_url': reverse_course_url('course_handler', course_key),
        'language_options': settings.ALL_LANGUAGES,
        'credit_eligibility_enabled': credit_eligibility_enabled,
        'is_credit_course': False,
        'show_min_grade_warning': False,
        'enrollment_end_editable': enrollment_end_editable,
        'is_prerequisite_courses_enabled': is_prerequisite_courses_enabled(),
        'is_entrance_exams_enabled': core_toggles.ENTRANCE_EXAMS.is_enabled(),
        'enable_extended_course_details': enable_extended_course_details,
        'upgrade_deadline': upgrade_deadline,
        'mfe_proctored_exam_settings_url': get_proctored_exam_settings_url(course_block.id),
    }
    if is_prerequisite_courses_enabled():
        courses, in_process_course_actions = get_courses_accessible_to_user(request)
        # exclude current course from the list of available courses
        courses = [course for course in courses if course.id != course_key]
        if courses:
            courses, __ = _process_courses_list(courses, in_process_course_actions)
        settings_context.update({'possible_pre_requisite_courses': courses})

    if credit_eligibility_enabled:
        if is_credit_course(course_key):
            # get and all credit eligibility requirements
            credit_requirements = get_credit_requirements(course_key)
            # pair together requirements with same 'namespace' values
            paired_requirements = {}
            for requirement in credit_requirements:
                namespace = requirement.pop("namespace")
                paired_requirements.setdefault(namespace, []).append(requirement)

            # if 'minimum_grade_credit' of a course is not set or 0 then
            # show warning message to course author.
            show_min_grade_warning = False if course_block.minimum_grade_credit > 0 else True  # lint-amnesty, pylint: disable=simplifiable-if-expression
            settings_context.update(
                {
                    'is_credit_course': True,
                    'credit_requirements': paired_requirements,
                    'show_min_grade_warning': show_min_grade_warning,
                }
            )

    return settings_context


def get_course_grading(course_key):
    """
    Utils is used to get context of course grading.
    It is used for both DRF and django views.
    """

    course_block = modulestore().get_course(course_key)
    course_details = CourseGradingModel.fetch(course_key)
    course_assignment_lists = get_subsections_by_assignment_type(course_key)
    grading_context = {
        'context_course': course_block,
        'course_locator': course_key,
        'course_details': course_details,
        'grading_url': reverse_course_url('grading_handler', course_key),
        'is_credit_course': is_credit_course(course_key),
        'mfe_proctored_exam_settings_url': get_proctored_exam_settings_url(course_key),
        'course_assignment_lists': dict(course_assignment_lists)
    }

    return grading_context


class StudioPermissionsService:
    """
    Service that can provide information about a user's permissions.

    Deprecated. To be replaced by a more general authorization service.

    Only used by LibraryContentBlock (and library_tools.py).
    """

    def __init__(self, user):
        self._user = user

    def can_read(self, course_key):
        """ Does the user have read access to the given course/library? """
        return has_studio_read_access(self._user, course_key)

    def can_write(self, course_key):
        """ Does the user have read access to the given course/library? """
        return has_studio_write_access(self._user, course_key)
