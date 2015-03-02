"""This file contains (or should), all access control logic for the courseware.
Ideally, it will be the only place that needs to know about any special settings
like DISABLE_START_DATES"""
import logging
from datetime import datetime, timedelta
import pytz

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from xmodule.course_module import (
    CourseDescriptor, CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
    CATALOG_VISIBILITY_ABOUT)
from xmodule.error_module import ErrorDescriptor
from xmodule.x_module import XModule
from xmodule.split_test_module import get_split_user_partitions

from xblock.core import XBlock
from xmodule.partitions.partitions import NoSuchUserPartitionError, NoSuchUserPartitionGroupError

from external_auth.models import ExternalAuthMap
from courseware.masquerade import get_masquerade_role, is_masquerading_as_student
from django.utils.timezone import UTC
from student import auth
from student.roles import (
    GlobalStaff, CourseStaffRole, CourseInstructorRole,
    OrgStaffRole, OrgInstructorRole, CourseBetaTesterRole
)
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from opaque_keys.edx.keys import CourseKey, UsageKey
from util.milestones_helpers import get_pre_requisite_courses_not_completed
DEBUG_ACCESS = False

log = logging.getLogger(__name__)


def debug(*args, **kwargs):
    # to avoid overly verbose output, this is off by default
    if DEBUG_ACCESS:
        log.debug(*args, **kwargs)


def has_access(user, action, obj, course_key=None):
    """
    Check whether a user has the access to do action on obj.  Handles any magic
    switching based on various settings.

    Things this module understands:
    - start dates for modules
    - visible_to_staff_only for modules
    - DISABLE_START_DATES
    - different access for instructor, staff, course staff, and students.
    - mobile_available flag for course modules

    user: a Django user object. May be anonymous. If none is passed,
                    anonymous is assumed

    obj: The object to check access for.  A module, descriptor, location, or
                    certain special strings (e.g. 'global')

    action: A string specifying the action that the client is trying to perform.

    actions depend on the obj type, but include e.g. 'enroll' for courses.  See the
    type-specific functions below for the known actions for that type.

    course_key: A course_key specifying which course run this access is for.
        Required when accessing anything other than a CourseDescriptor, 'global',
        or a location with category 'course'

    Returns a bool.  It is up to the caller to actually deny access in a way
    that makes sense in context.
    """
    # Just in case user is passed in as None, make them anonymous
    if not user:
        user = AnonymousUser()

    # delegate the work to type-specific functions.
    # (start with more specific types, then get more general)
    if isinstance(obj, CourseDescriptor):
        return _has_access_course_desc(user, action, obj)

    if isinstance(obj, ErrorDescriptor):
        return _has_access_error_desc(user, action, obj, course_key)

    if isinstance(obj, XModule):
        return _has_access_xmodule(user, action, obj, course_key)

    # NOTE: any descriptor access checkers need to go above this
    if isinstance(obj, XBlock):
        return _has_access_descriptor(user, action, obj, course_key)

    if isinstance(obj, CourseKey):
        return _has_access_course_key(user, action, obj)

    if isinstance(obj, UsageKey):
        return _has_access_location(user, action, obj, course_key)

    if isinstance(obj, basestring):
        return _has_access_string(user, action, obj)

    # Passing an unknown object here is a coding error, so rather than
    # returning a default, complain.
    raise TypeError("Unknown object type in has_access(): '{0}'"
                    .format(type(obj)))


# ================ Implementation helpers ================================
def _has_access_course_desc(user, action, course):
    """
    Check if user has access to a course descriptor.

    Valid actions:

    'load' -- load the courseware, see inside the course
    'load_forum' -- can load and contribute to the forums (one access level for now)
    'load_mobile' -- can load from a mobile context
    'load_mobile_no_enrollment_check' -- can load from a mobile context without checking for enrollment
    'enroll' -- enroll.  Checks for enrollment window,
                  ACCESS_REQUIRE_STAFF_FOR_COURSE,
    'see_exists' -- can see that the course exists.
    'staff' -- staff access to course.
    'see_in_catalog' -- user is able to see the course listed in the course catalog.
    'see_about_page' -- user is able to see the course about page.
    """
    def can_load():
        """
        Can this user load this course?

        NOTE: this is not checking whether user is actually enrolled in the course.
        """
        # delegate to generic descriptor check to check start dates
        return _has_access_descriptor(user, 'load', course, course.id)

    def can_load_forum():
        """
        Can this user access the forums in this course?
        """
        return (
            can_load() and
            (
                CourseEnrollment.is_enrolled(user, course.id) or
                _has_staff_access_to_descriptor(user, course, course.id)
            )
        )

    def can_load_mobile():
        """
        Can this user access this course from a mobile device?
        """
        return (
            # check mobile requirements
            can_load_mobile_no_enroll_check() and
            # check enrollment
            (
                CourseEnrollment.is_enrolled(user, course.id) or
                _has_staff_access_to_descriptor(user, course, course.id)
            )
        )

    def can_load_mobile_no_enroll_check():
        """
        Can this enrolled user access this course from a mobile device?
        Note: does not check for enrollment since it is assumed the caller has done so.
        """
        return (
            # check start date
            can_load() and
            # check mobile_available flag
            is_mobile_available_for_user(user, course)
        )

    def can_enroll():
        """
        First check if restriction of enrollment by login method is enabled, both
            globally and by the course.
        If it is, then the user must pass the criterion set by the course, e.g. that ExternalAuthMap
            was set by 'shib:https://idp.stanford.edu/", in addition to requirements below.
        Rest of requirements:
        (CourseEnrollmentAllowed always overrides)
          or
        (staff can always enroll)
          or
        Enrollment can only happen in the course enrollment period, if one exists, and
        course is not invitation only.
        """

        # if using registration method to restrict (say shibboleth)
        if settings.FEATURES.get('RESTRICT_ENROLL_BY_REG_METHOD') and course.enrollment_domain:
            if user is not None and user.is_authenticated() and \
                    ExternalAuthMap.objects.filter(user=user, external_domain=course.enrollment_domain):
                debug("Allow: external_auth of " + course.enrollment_domain)
                reg_method_ok = True
            else:
                reg_method_ok = False
        else:
            reg_method_ok = True  # if not using this access check, it's always OK.

        now = datetime.now(UTC())
        start = course.enrollment_start or datetime.min.replace(tzinfo=pytz.UTC)
        end = course.enrollment_end or datetime.max.replace(tzinfo=pytz.UTC)

        # if user is in CourseEnrollmentAllowed with right course key then can also enroll
        # (note that course.id actually points to a CourseKey)
        # (the filter call uses course_id= since that's the legacy database schema)
        # (sorry that it's confusing :( )
        if user is not None and user.is_authenticated() and CourseEnrollmentAllowed:
            if CourseEnrollmentAllowed.objects.filter(email=user.email, course_id=course.id):
                return True

        if _has_staff_access_to_descriptor(user, course, course.id):
            return True

        # Invitation_only doesn't apply to CourseEnrollmentAllowed or has_staff_access_access
        if course.invitation_only:
            debug("Deny: invitation only")
            return False

        if reg_method_ok and start < now < end:
            debug("Allow: in enrollment period")
            return True

    def see_exists():
        """
        Can see if can enroll, but also if can load it: if user enrolled in a course and now
        it's past the enrollment period, they should still see it.

        TODO (vshnayder): This means that courses with limited enrollment periods will not appear
        to non-staff visitors after the enrollment period is over.  If this is not what we want, will
        need to change this logic.
        """
        # VS[compat] -- this setting should go away once all courses have
        # properly configured enrollment_start times (if course should be
        # staff-only, set enrollment_start far in the future.)
        if settings.FEATURES.get('ACCESS_REQUIRE_STAFF_FOR_COURSE'):
            # if this feature is on, only allow courses that have ispublic set to be
            # seen by non-staff
            if course.ispublic:
                debug("Allow: ACCESS_REQUIRE_STAFF_FOR_COURSE and ispublic")
                return True
            return _has_staff_access_to_descriptor(user, course, course.id)

        return can_enroll() or can_load()

    def can_see_in_catalog():
        """
        Implements the "can see course in catalog" logic if a course should be visible in the main course catalog
        In this case we use the catalog_visibility property on the course descriptor
        but also allow course staff to see this.
        """
        return (
            course.catalog_visibility == CATALOG_VISIBILITY_CATALOG_AND_ABOUT or
            _has_staff_access_to_descriptor(user, course, course.id)
        )

    def can_see_about_page():
        """
        Implements the "can see course about page" logic if a course about page should be visible
        In this case we use the catalog_visibility property on the course descriptor
        but also allow course staff to see this.
        """
        return (
            course.catalog_visibility == CATALOG_VISIBILITY_CATALOG_AND_ABOUT or
            course.catalog_visibility == CATALOG_VISIBILITY_ABOUT or
            _has_staff_access_to_descriptor(user, course, course.id)
        )

    def can_view_courseware_with_prerequisites():  # pylint: disable=invalid-name
        """
        Checks if prerequisite courses feature is enabled and course has prerequisites
        and user is neither staff nor anonymous then it returns False if user has not
        passed prerequisite courses otherwise return True.
        """
        if settings.FEATURES['ENABLE_PREREQUISITE_COURSES'] \
                and not _has_staff_access_to_descriptor(user, course, course.id) \
                and course.pre_requisite_courses \
                and not user.is_anonymous() \
                and get_pre_requisite_courses_not_completed(user, [course.id]):
            return False
        else:
            return True

    checkers = {
        'load': can_load,
        'view_courseware_with_prerequisites': can_view_courseware_with_prerequisites,
        'load_forum': can_load_forum,
        'load_mobile': can_load_mobile,
        'load_mobile_no_enrollment_check': can_load_mobile_no_enroll_check,
        'enroll': can_enroll,
        'see_exists': see_exists,
        'staff': lambda: _has_staff_access_to_descriptor(user, course, course.id),
        'instructor': lambda: _has_instructor_access_to_descriptor(user, course, course.id),
        'see_in_catalog': can_see_in_catalog,
        'see_about_page': can_see_about_page,
    }

    return _dispatch(checkers, action, user, course)


def _has_access_error_desc(user, action, descriptor, course_key):
    """
    Only staff should see error descriptors.

    Valid actions:
    'load' -- load this descriptor, showing it to the user.
    'staff' -- staff access to descriptor.
    """
    def check_for_staff():
        return _has_staff_access_to_descriptor(user, descriptor, course_key)

    checkers = {
        'load': check_for_staff,
        'staff': check_for_staff,
        'instructor': lambda: _has_instructor_access_to_descriptor(user, descriptor, course_key)
    }

    return _dispatch(checkers, action, user, descriptor)


def _has_group_access(descriptor, user, course_key):
    """
    This function returns a boolean indicating whether or not `user` has
    sufficient group memberships to "load" a block (the `descriptor`)
    """
    if len(descriptor.user_partitions) == len(get_split_user_partitions(descriptor.user_partitions)):
        # Short-circuit the process, since there are no defined user partitions that are not
        # user_partitions used by the split_test module. The split_test module handles its own access
        # via updating the children of the split_test module.
        return True

    # use merged_group_access which takes group access on the block's
    # parents / ancestors into account
    merged_access = descriptor.merged_group_access
    # check for False in merged_access, which indicates that at least one
    # partition's group list excludes all students.
    if False in merged_access.values():
        log.warning("Group access check excludes all students, access will be denied.", exc_info=True)
        return False

    # resolve the partition IDs in group_access to actual
    # partition objects, skipping those which contain empty group directives.
    # if a referenced partition could not be found, access will be denied.
    try:
        partitions = [
            descriptor._get_user_partition(partition_id)  # pylint:disable=protected-access
            for partition_id, group_ids in merged_access.items()
            if group_ids is not None
        ]
    except NoSuchUserPartitionError:
        log.warning("Error looking up user partition, access will be denied.", exc_info=True)
        return False

    # next resolve the group IDs specified within each partition
    partition_groups = []
    try:
        for partition in partitions:
            groups = [
                partition.get_group(group_id)
                for group_id in merged_access[partition.id]
            ]
            if groups:
                partition_groups.append((partition, groups))
    except NoSuchUserPartitionGroupError:
        log.warning("Error looking up referenced user partition group, access will be denied.", exc_info=True)
        return False

    # look up the user's group for each partition
    user_groups = {}
    for partition, groups in partition_groups:
        user_groups[partition.id] = partition.scheme.get_group_for_user(
            course_key,
            user,
            partition,
        )

    # finally: check that the user has a satisfactory group assignment
    # for each partition.
    if not all(user_groups.get(partition.id) in groups for partition, groups in partition_groups):
        return False

    # all checks passed.
    return True


def _has_access_descriptor(user, action, descriptor, course_key=None):
    """
    Check if user has access to this descriptor.

    Valid actions:
    'load' -- load this descriptor, showing it to the user.
    'staff' -- staff access to descriptor.

    NOTE: This is the fallback logic for descriptors that don't have custom policy
    (e.g. courses).  If you call this method directly instead of going through
    has_access(), it will not do the right thing.
    """
    def can_load():
        """
        NOTE: This does not check that the student is enrolled in the course
        that contains this module.  We may or may not want to allow non-enrolled
        students to see modules.  If not, views should check the course, so we
        don't have to hit the enrollments table on every module load.
        """
        if descriptor.visible_to_staff_only and not _has_staff_access_to_descriptor(user, descriptor, course_key):
            return False

        # enforce group access
        if not _has_group_access(descriptor, user, course_key):
            # if group_access check failed, deny access unless the requestor is staff,
            # in which case immediately grant access.
            return _has_staff_access_to_descriptor(user, descriptor, course_key)

        # If start dates are off, can always load
        if settings.FEATURES['DISABLE_START_DATES'] and not is_masquerading_as_student(user, course_key):
            debug("Allow: DISABLE_START_DATES")
            return True

        # Check start date
        if 'detached' not in descriptor._class_tags and descriptor.start is not None:
            now = datetime.now(UTC())
            effective_start = _adjust_start_date_for_beta_testers(
                user,
                descriptor,
                course_key=course_key
            )
            if now > effective_start:
                # after start date, everyone can see it
                debug("Allow: now > effective start date")
                return True
            # otherwise, need staff access
            return _has_staff_access_to_descriptor(user, descriptor, course_key)

        # No start date, so can always load.
        debug("Allow: no start date")
        return True

    checkers = {
        'load': can_load,
        'staff': lambda: _has_staff_access_to_descriptor(user, descriptor, course_key),
        'instructor': lambda: _has_instructor_access_to_descriptor(user, descriptor, course_key)
    }

    return _dispatch(checkers, action, user, descriptor)


def _has_access_xmodule(user, action, xmodule, course_key):
    """
    Check if user has access to this xmodule.

    Valid actions:
      - same as the valid actions for xmodule.descriptor
    """
    # Delegate to the descriptor
    return has_access(user, action, xmodule.descriptor, course_key)


def _has_access_location(user, action, location, course_key):
    """
    Check if user has access to this location.

    Valid actions:
    'staff' : True if the user has staff access to this location

    NOTE: if you add other actions, make sure that

     has_access(user, location, action) == has_access(user, get_item(location), action)
    """
    checkers = {
        'staff': lambda: _has_staff_access_to_location(user, location, course_key)
    }

    return _dispatch(checkers, action, user, location)


def _has_access_course_key(user, action, course_key):
    """
    Check if user has access to the course with this course_key

    Valid actions:
    'staff' : True if the user has staff access to this location
    'instructor' : True if the user has staff access to this location
    """
    checkers = {
        'staff': lambda: _has_staff_access_to_location(user, None, course_key),
        'instructor': lambda: _has_instructor_access_to_location(user, None, course_key),
    }

    return _dispatch(checkers, action, user, course_key)


def _has_access_string(user, action, perm):
    """
    Check if user has certain special access, specified as string.  Valid strings:

    'global'

    Valid actions:

    'staff' -- global staff access.
    """

    def check_staff():
        if perm != 'global':
            debug("Deny: invalid permission '%s'", perm)
            return False
        return GlobalStaff().has_user(user)

    checkers = {
        'staff': check_staff
    }

    return _dispatch(checkers, action, user, perm)


#####  Internal helper methods below

def _dispatch(table, action, user, obj):
    """
    Helper: call table[action], raising a nice pretty error if there is no such key.

    user and object passed in only for error messages and debugging
    """
    if action in table:
        result = table[action]()
        debug("%s user %s, object %s, action %s",
              'ALLOWED' if result else 'DENIED',
              user,
              obj.location.to_deprecated_string() if isinstance(obj, XBlock) else str(obj),
              action)
        return result

    raise ValueError(u"Unknown action for object type '{0}': '{1}'".format(
        type(obj), action))


def _adjust_start_date_for_beta_testers(user, descriptor, course_key=None):  # pylint: disable=invalid-name
    """
    If user is in a beta test group, adjust the start date by the appropriate number of
    days.

    Arguments:
       user: A django user.  May be anonymous.
       descriptor: the XModuleDescriptor the user is trying to get access to, with a
       non-None start date.

    Returns:
        A datetime.  Either the same as start, or earlier for beta testers.

    NOTE: number of days to adjust should be cached to avoid looking it up thousands of
    times per query.

    NOTE: For now, this function assumes that the descriptor's location is in the course
    the user is looking at.  Once we have proper usages and definitions per the XBlock
    design, this should use the course the usage is in.

    NOTE: If testing manually, make sure FEATURES['DISABLE_START_DATES'] = False
    in envs/dev.py!
    """
    if descriptor.days_early_for_beta is None:
        # bail early if no beta testing is set up
        return descriptor.start

    if CourseBetaTesterRole(course_key).has_user(user):
        debug("Adjust start time: user in beta role for %s", descriptor)
        delta = timedelta(descriptor.days_early_for_beta)
        effective = descriptor.start - delta
        return effective

    return descriptor.start


def _has_instructor_access_to_location(user, location, course_key=None):
    if course_key is None:
        course_key = location.course_key
    return _has_access_to_course(user, 'instructor', course_key)


def _has_staff_access_to_location(user, location, course_key=None):
    if course_key is None:
        course_key = location.course_key
    return _has_access_to_course(user, 'staff', course_key)


def _has_access_to_course(user, access_level, course_key):
    '''
    Returns True if the given user has access_level (= staff or
    instructor) access to the course with the given course_key.
    This ensures the user is authenticated and checks if global staff or has
    staff / instructor access.

    access_level = string, either "staff" or "instructor"
    '''
    if user is None or (not user.is_authenticated()):
        debug("Deny: no user or anon user")
        return False

    if is_masquerading_as_student(user, course_key):
        return False

    if GlobalStaff().has_user(user):
        debug("Allow: user.is_staff")
        return True

    if access_level not in ('staff', 'instructor'):
        log.debug("Error in access._has_access_to_course access_level=%s unknown", access_level)
        debug("Deny: unknown access level")
        return False

    staff_access = (
        CourseStaffRole(course_key).has_user(user) or
        OrgStaffRole(course_key.org).has_user(user)
    )

    if staff_access and access_level == 'staff':
        debug("Allow: user has course staff access")
        return True

    instructor_access = (
        CourseInstructorRole(course_key).has_user(user) or
        OrgInstructorRole(course_key.org).has_user(user)
    )

    if instructor_access and access_level in ('staff', 'instructor'):
        debug("Allow: user has course instructor access")
        return True

    debug("Deny: user did not have correct access")
    return False


def _has_instructor_access_to_descriptor(user, descriptor, course_key):  # pylint: disable=invalid-name
    """Helper method that checks whether the user has staff access to
    the course of the location.

    descriptor: something that has a location attribute
    """
    return _has_instructor_access_to_location(user, descriptor.location, course_key)


def _has_staff_access_to_descriptor(user, descriptor, course_key):
    """Helper method that checks whether the user has staff access to
    the course of the location.

    descriptor: something that has a location attribute
    """
    return _has_staff_access_to_location(user, descriptor.location, course_key)


def is_mobile_available_for_user(user, course):
    """
    Returns whether the given course is mobile_available for the given user.
    Checks:
        mobile_available flag on the course
        Beta User and staff access overrides the mobile_available flag
    """
    return (
        course.mobile_available or
        auth.has_access(user, CourseBetaTesterRole(course.id)) or
        _has_staff_access_to_descriptor(user, course, course.id)
    )


def get_user_role(user, course_key):
    """
    Return corresponding string if user has staff, instructor or student
    course role in LMS.
    """
    role = get_masquerade_role(user, course_key)
    if role:
        return role
    elif has_access(user, 'instructor', course_key):
        return 'instructor'
    elif has_access(user, 'staff', course_key):
        return 'staff'
    else:
        return 'student'
