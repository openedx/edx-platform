"""
Common utility functions useful throughout the contentstore
"""

import logging
from datetime import datetime
from pytz import UTC

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django_comment_common.models import assign_default_role
from django_comment_common.utils import seed_permissions_roles

from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from opaque_keys.edx.keys import UsageKey, CourseKey
from student.roles import CourseInstructorRole, CourseStaffRole
from student.models import CourseEnrollment
from student import auth


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


def delete_course_and_groups(course_key, user_id):
    """
    This deletes the courseware associated with a course_key as well as cleaning update_item
    the various user table stuff (groups, permissions, etc.)
    """
    module_store = modulestore()

    with module_store.bulk_operations(course_key):
        module_store.delete_course(course_key, user_id)

        print 'removing User permissions from course....'
        # in the django layer, we need to remove all the user permissions groups associated with this course
        try:
            remove_all_instructors(course_key)
        except Exception as err:
            log.error("Error in deleting course groups for {0}: {1}".format(course_key, err))


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

    return u"//{lms_base}/courses/{course_key}/jump_to/{location}".format(
        lms_base=lms_base,
        course_key=location.course_key.to_deprecated_string(),
        location=location.to_deprecated_string(),
    )


# pylint: disable=invalid-name
def get_lms_link_for_certificate_web_view(user_id, course_key, mode):
    """
    Returns the url to the certificate web view.
    """
    assert isinstance(course_key, CourseKey)

    if settings.LMS_BASE is None:
        return None

    return u"//{certificate_web_base}/certificates/user/{user_id}/course/{course_id}?preview={mode}".format(
        certificate_web_base=settings.LMS_BASE,
        user_id=user_id,
        course_id=unicode(course_key),
        mode=mode
    )


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
    if 'detached' not in published._class_tags and published.start is not None:
        return datetime.now(UTC) > published.start

    # No start date, so it's always visible
    return True


def has_children_visible_to_specific_content_groups(xblock):
    """
    Returns True if this xblock has children that are limited to specific content groups.
    Note that this method is not recursive (it does not check grandchildren).
    """
    if not xblock.has_children:
        return False

    for child in xblock.get_children():
        if is_visible_to_specific_content_groups(child):
            return True

    return False


def is_visible_to_specific_content_groups(xblock):
    """
    Returns True if this xblock has visibility limited to specific content groups.
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
    kwargs_for_reverse = {key_name: unicode(key_value)} if key_name else None
    if kwargs:
        kwargs_for_reverse.update(kwargs)
    return reverse('contentstore.views.' + handler_name, kwargs=kwargs_for_reverse)


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
    for p in sorted(course.user_partitions, key=lambda p: p.name):

        # Exclude disabled partitions, partitions with no groups defined
        # Also filter by scheme name if there's a filter defined.
        if p.active and p.groups and (schemes is None or p.scheme.name in schemes):

            # First, add groups defined by the partition
            groups = []
            for g in p.groups:

                # Falsey group access for a partition mean that all groups
                # are selected.  In the UI, though, we don't show the particular
                # groups selected, since there's a separate option for "all users".
                selected_groups = set(xblock.group_access.get(p.id, []) or [])
                groups.append({
                    "id": g.id,
                    "name": g.name,
                    "selected": g.id in selected_groups,
                    "deleted": False,
                })

            # Next, add any groups set on the XBlock that have been deleted
            all_groups = set(g.id for g in p.groups)
            missing_group_ids = selected_groups - all_groups
            for gid in missing_group_ids:
                groups.append({
                    "id": gid,
                    "name": _("Deleted group"),
                    "selected": True,
                    "deleted": True,
                })

            # Put together the entire partition dictionary
            partitions.append({
                "id": p.id,
                "name": p.name,
                "scheme": p.scheme.name,
                "groups": groups,
            })

    return partitions


def get_visibility_partition_info(xblock):
    """
    Retrieve user partition information for the component visibility editor.

    This pre-processes partition information to simplify the template.

    Arguments:
        xblock (XBlock): The component being edited.

    Returns: dict

    """
    user_partitions = get_user_partition_info(xblock, schemes=["verification", "cohort"])
    cohort_partitions = []
    verification_partitions = []
    has_selected_groups = False
    selected_verified_partition_id = None

    # Pre-process the partitions to make it easier to display the UI
    for p in user_partitions:
        has_selected = any(g["selected"] for g in p["groups"])
        has_selected_groups = has_selected_groups or has_selected

        if p["scheme"] == "cohort":
            cohort_partitions.append(p)
        elif p["scheme"] == "verification":
            verification_partitions.append(p)
            if has_selected:
                selected_verified_partition_id = p["id"]

    return {
        "user_partitions": user_partitions,
        "cohort_partitions": cohort_partitions,
        "verification_partitions": verification_partitions,
        "has_selected_groups": has_selected_groups,
        "selected_verified_partition_id": selected_verified_partition_id,
    }


def is_self_paced(course):
    """
    Returns True if course is self-paced, False otherwise.
    """
    return course and course.self_paced and SelfPacedConfiguration.current().enabled
