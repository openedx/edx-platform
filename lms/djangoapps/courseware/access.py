"""This file contains (or should), all access control logic for the courseware.
Ideally, it will be the only place that needs to know about any special settings
like DISABLE_START_DATES"""
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from xmodule.course_module import CourseDescriptor
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore import Location
from xmodule.x_module import XModule

from xblock.core import XBlock

from student.models import CourseEnrollmentAllowed
from external_auth.models import ExternalAuthMap
from courseware.masquerade import is_masquerading_as_student
from django.utils.timezone import UTC
from student.models import CourseEnrollment
from student.roles import (
    GlobalStaff, CourseStaffRole, CourseInstructorRole,
    OrgStaffRole, OrgInstructorRole, CourseBetaTesterRole
)
DEBUG_ACCESS = False

log = logging.getLogger(__name__)


def debug(*args, **kwargs):
    # to avoid overly verbose output, this is off by default
    if DEBUG_ACCESS:
        log.debug(*args, **kwargs)


def has_access(user, obj, action, course_context=None):
    """
    Check whether a user has the access to do action on obj.  Handles any magic
    switching based on various settings.

    Things this module understands:
    - start dates for modules
    - DISABLE_START_DATES
    - different access for instructor, staff, course staff, and students.

    user: a Django user object. May be anonymous. If none is passed,
                    anonymous is assumed

    obj: The object to check access for.  A module, descriptor, location, or
                    certain special strings (e.g. 'global')

    action: A string specifying the action that the client is trying to perform.

    actions depend on the obj type, but include e.g. 'enroll' for courses.  See the
    type-specific functions below for the known actions for that type.

    course_context: A course_id specifying which course run this access is for.
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
        return _has_access_course_desc(user, obj, action)

    if isinstance(obj, ErrorDescriptor):
        return _has_access_error_desc(user, obj, action, course_context)

    if isinstance(obj, XModule):
        return _has_access_xmodule(user, obj, action, course_context)

    # NOTE: any descriptor access checkers need to go above this
    if isinstance(obj, XBlock):
        return _has_access_descriptor(user, obj, action, course_context)

    if isinstance(obj, Location):
        return _has_access_location(user, obj, action, course_context)

    if isinstance(obj, basestring):
        return _has_access_string(user, obj, action, course_context)

    # Passing an unknown object here is a coding error, so rather than
    # returning a default, complain.
    raise TypeError("Unknown object type in has_access(): '{0}'"
                    .format(type(obj)))


# ================ Implementation helpers ================================
def _has_access_course_desc(user, course, action):
    """
    Check if user has access to a course descriptor.

    Valid actions:

    'load' -- load the courseware, see inside the course
    'load_forum' -- can load and contribute to the forums (one access level for now)
    'enroll' -- enroll.  Checks for enrollment window,
                  ACCESS_REQUIRE_STAFF_FOR_COURSE,
    'see_exists' -- can see that the course exists.
    'staff' -- staff access to course.
    """
    def can_load():
        """
        Can this user load this course?

        NOTE: this is not checking whether user is actually enrolled in the course.
        """
        # delegate to generic descriptor check to check start dates
        return _has_access_descriptor(user, course, 'load')

    def can_load_forum():
        """
        Can this user access the forums in this course?
        """
        return (can_load() and \
            (CourseEnrollment.is_enrolled(user, course.id) or \
                _has_staff_access_to_descriptor(user, course)
            ))

    def can_enroll():
        """
        First check if restriction of enrollment by login method is enabled, both
            globally and by the course.
        If it is, then the user must pass the criterion set by the course, e.g. that ExternalAuthMap
            was set by 'shib:https://idp.stanford.edu/", in addition to requirements below.
        Rest of requirements:
        Enrollment can only happen in the course enrollment period, if one exists.
            or

        (CourseEnrollmentAllowed always overrides)
        (staff can always enroll)
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
            reg_method_ok = True #if not using this access check, it's always OK.

        now = datetime.now(UTC())
        start = course.enrollment_start
        end = course.enrollment_end

        if reg_method_ok and (start is None or now > start) and (end is None or now < end):
            # in enrollment period, so any user is allowed to enroll.
            debug("Allow: in enrollment period")
            return True

        # if user is in CourseEnrollmentAllowed with right course_id then can also enroll
        if user is not None and user.is_authenticated() and CourseEnrollmentAllowed:
            if CourseEnrollmentAllowed.objects.filter(email=user.email, course_id=course.id):
                return True

        # otherwise, need staff access
        return _has_staff_access_to_descriptor(user, course)

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
            return _has_staff_access_to_descriptor(user, course)

        return can_enroll() or can_load()

    checkers = {
        'load': can_load,
        'load_forum': can_load_forum,
        'enroll': can_enroll,
        'see_exists': see_exists,
        'staff': lambda: _has_staff_access_to_descriptor(user, course),
        'instructor': lambda: _has_instructor_access_to_descriptor(user, course),
        }

    return _dispatch(checkers, action, user, course)


def _has_access_error_desc(user, descriptor, action, course_context):
    """
    Only staff should see error descriptors.

    Valid actions:
    'load' -- load this descriptor, showing it to the user.
    'staff' -- staff access to descriptor.
    """
    def check_for_staff():
        return _has_staff_access_to_descriptor(user, descriptor, course_context)

    checkers = {
        'load': check_for_staff,
        'staff': check_for_staff
        }

    return _dispatch(checkers, action, user, descriptor)


def _has_access_descriptor(user, descriptor, action, course_context=None):
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
        # If start dates are off, can always load
        if settings.FEATURES['DISABLE_START_DATES'] and not is_masquerading_as_student(user):
            debug("Allow: DISABLE_START_DATES")
            return True

        # Check start date
        if 'detached' not in descriptor._class_tags and descriptor.start is not None:
            now = datetime.now(UTC())
            effective_start = _adjust_start_date_for_beta_testers(
                user,
                descriptor,
                course_context=course_context
            )
            if now > effective_start:
                # after start date, everyone can see it
                debug("Allow: now > effective start date")
                return True
            # otherwise, need staff access
            return _has_staff_access_to_descriptor(user, descriptor, course_context)

        # No start date, so can always load.
        debug("Allow: no start date")
        return True

    checkers = {
        'load': can_load,
        'staff': lambda: _has_staff_access_to_descriptor(user, descriptor, course_context)
        }

    return _dispatch(checkers, action, user, descriptor)


def _has_access_xmodule(user, xmodule, action, course_context):
    """
    Check if user has access to this xmodule.

    Valid actions:
      - same as the valid actions for xmodule.descriptor
    """
    # Delegate to the descriptor
    return has_access(user, xmodule.descriptor, action, course_context)


def _has_access_location(user, location, action, course_context):
    """
    Check if user has access to this location.

    Valid actions:
    'staff' : True if the user has staff access to this location

    NOTE: if you add other actions, make sure that

     has_access(user, location, action) == has_access(user, get_item(location), action)

    And in general, prefer checking access on loaded items, rather than locations.
    """
    checkers = {
        'staff': lambda: _has_staff_access_to_location(user, location, course_context)
        }

    return _dispatch(checkers, action, user, location)


def _has_access_string(user, perm, action, course_context):
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
              obj.location.url() if isinstance(obj, XBlock) else str(obj)[:60],
              action)
        return result

    raise ValueError(u"Unknown action for object type '{0}': '{1}'".format(
        type(obj), action))


def _adjust_start_date_for_beta_testers(user, descriptor, course_context=None):
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

    if CourseBetaTesterRole(descriptor.location, course_context=course_context).has_user(user):
        debug("Adjust start time: user in beta role for %s", descriptor)
        delta = timedelta(descriptor.days_early_for_beta)
        effective = descriptor.start - delta
        return effective

    return descriptor.start


def _has_instructor_access_to_location(user, location, course_context=None):
    return _has_access_to_location(user, location, 'instructor', course_context)


def _has_staff_access_to_location(user, location, course_context=None):
    return _has_access_to_location(user, location, 'staff', course_context)


def _has_access_to_location(user, location, access_level, course_context):
    '''
    Returns True if the given user has access_level (= staff or
    instructor) access to a location.  For now this is equivalent to
    having staff / instructor access to the course location.course.

    This means that user is in the staff_* group or instructor_* group, or is an overall admin.

    TODO (vshnayder): this needs to be changed to allow per-course_id permissions, not per-course
    (e.g. staff in 2012 is different from 2013, but maybe some people always have access)

    course is a string: the course field of the location being accessed.
    location = location
    access_level = string, either "staff" or "instructor"
    '''
    if user is None or (not user.is_authenticated()):
        debug("Deny: no user or anon user")
        return False

    if is_masquerading_as_student(user):
        return False

    if GlobalStaff().has_user(user):
        debug("Allow: user.is_staff")
        return True

    if access_level not in ('staff', 'instructor'):
        log.debug("Error in access._has_access_to_location access_level=%s unknown", access_level)
        debug("Deny: unknown access level")
        return False

    staff_access = (
        CourseStaffRole(location, course_context).has_user(user) or
        OrgStaffRole(location).has_user(user)
    )

    if staff_access and access_level == 'staff':
        debug("Allow: user has course staff access")
        return True

    instructor_access = (
        CourseInstructorRole(location, course_context).has_user(user) or
        OrgInstructorRole(location).has_user(user)
    )

    if instructor_access and access_level in ('staff', 'instructor'):
        debug("Allow: user has course instructor access")
        return True

    debug("Deny: user did not have correct access")
    return False


def _has_staff_access_to_course_id(user, course_id):
    """Helper method that takes a course_id instead of a course name"""
    loc = CourseDescriptor.id_to_location(course_id)
    return _has_staff_access_to_location(user, loc, course_id)


def _has_instructor_access_to_descriptor(user, descriptor, course_context=None):
    """Helper method that checks whether the user has staff access to
    the course of the location.

    descriptor: something that has a location attribute
    """
    return _has_instructor_access_to_location(user, descriptor.location, course_context)


def _has_staff_access_to_descriptor(user, descriptor, course_context=None):
    """Helper method that checks whether the user has staff access to
    the course of the location.

    descriptor: something that has a location attribute
    """
    return _has_staff_access_to_location(user, descriptor.location, course_context)


def get_user_role(user, course_id):
    """
    Return corresponding string if user has staff, instructor or student
    course role in LMS.
    """
    from courseware.courses import get_course
    course = get_course(course_id)
    if is_masquerading_as_student(user):
        return 'student'
    elif has_access(user, course, 'instructor'):
        return 'instructor'
    elif has_access(user, course, 'staff'):
        return 'staff'
    else:
        return 'student'
