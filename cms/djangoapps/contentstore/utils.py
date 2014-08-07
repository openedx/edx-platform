# pylint: disable=E1103, E1101

import copy
import logging
import re
from datetime import datetime
from pytz import UTC

from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django_comment_common.models import assign_default_role
from django_comment_common.utils import seed_permissions_roles

from xmodule.contentstore.content import StaticContent
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from opaque_keys.edx.keys import UsageKey, CourseKey
from student.roles import CourseInstructorRole, CourseStaffRole
from student.models import CourseEnrollment
from student import auth


log = logging.getLogger(__name__)

# In order to instantiate an open ended tab automatically, need to have this data
OPEN_ENDED_PANEL = {"name": _("Open Ended Panel"), "type": "open_ended"}
NOTES_PANEL = {"name": _("My Notes"), "type": "notes"}
EXTRA_TAB_PANELS = dict([(p['type'], p) for p in [OPEN_ENDED_PANEL, NOTES_PANEL]])


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

    with module_store.bulk_write_operations(course_key):
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
    assert(isinstance(location, UsageKey))

    if settings.LMS_BASE is None:
        return None

    if preview:
        lms_base = settings.FEATURES.get('PREVIEW_LMS_BASE')
    else:
        lms_base = settings.LMS_BASE

    return u"//{lms_base}/courses/{course_key}/jump_to/{location}".format(
        lms_base=lms_base,
        course_key=location.course_key.to_deprecated_string(),
        location=location.to_deprecated_string(),
    )


def get_lms_link_for_about_page(course_key):
    """
    Returns the url to the course about page from the location tuple.
    """

    assert(isinstance(course_key, CourseKey))

    if settings.FEATURES.get('ENABLE_MKTG_SITE', False):
        if not hasattr(settings, 'MKTG_URLS'):
            log.exception("ENABLE_MKTG_SITE is True, but MKTG_URLS is not defined.")
            return None

        marketing_urls = settings.MKTG_URLS

        # Root will be "https://www.edx.org". The complete URL will still not be exactly correct,
        # but redirects exist from www.edx.org to get to the Drupal course about page URL.
        about_base = marketing_urls.get('ROOT', None)

        if about_base is None:
            log.exception('There is no ROOT defined in MKTG_URLS')
            return None

        # Strip off https:// (or http://) to be consistent with the formatting of LMS_BASE.
        about_base = re.sub(r"^https?://", "", about_base)

    elif settings.LMS_BASE is not None:
        about_base = settings.LMS_BASE
    else:
        return None

    return u"//{about_base_url}/courses/{course_key}/about".format(
        about_base_url=about_base,
        course_key=course_key.to_deprecated_string()
    )


def course_image_url(course):
    """Returns the image url for the course."""
    loc = StaticContent.compute_location(course.location.course_key, course.course_image)
    path = loc.to_deprecated_string()
    return path


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


def add_extra_panel_tab(tab_type, course):
    """
    Used to add the panel tab to a course if it does not exist.
    @param tab_type: A string representing the tab type.
    @param course: A course object from the modulestore.
    @return: Boolean indicating whether or not a tab was added and a list of tabs for the course.
    """
    # Copy course tabs
    course_tabs = copy.copy(course.tabs)
    changed = False
    # Check to see if open ended panel is defined in the course

    tab_panel = EXTRA_TAB_PANELS.get(tab_type)
    if tab_panel not in course_tabs:
        # Add panel to the tabs if it is not defined
        course_tabs.append(tab_panel)
        changed = True
    return changed, course_tabs


def remove_extra_panel_tab(tab_type, course):
    """
    Used to remove the panel tab from a course if it exists.
    @param tab_type: A string representing the tab type.
    @param course: A course object from the modulestore.
    @return: Boolean indicating whether or not a tab was added and a list of tabs for the course.
    """
    # Copy course tabs
    course_tabs = copy.copy(course.tabs)
    changed = False
    # Check to see if open ended panel is defined in the course

    tab_panel = EXTRA_TAB_PANELS.get(tab_type)
    if tab_panel in course_tabs:
        # Add panel to the tabs if it is not defined
        course_tabs = [ct for ct in course_tabs if ct != tab_panel]
        changed = True
    return changed, course_tabs


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


def reverse_usage_url(handler_name, usage_key, kwargs=None):
    """
    Creates the URL for handlers that use usage_keys as URL parameters.
    """
    return reverse_url(handler_name, 'usage_key_string', usage_key, kwargs)
