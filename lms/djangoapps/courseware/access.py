"""This file contains (or should), all access control logic for the courseware.
Ideally, it will be the only place that needs to know about any special settings
like DISABLE_START_DATES"""

import logging
import time

from django.conf import settings

from xmodule.course_module import CourseDescriptor
from xmodule.modulestore import Location
from xmodule.timeparse import parse_time
from xmodule.x_module import XModule, XModuleDescriptor


DEBUG_ACCESS = True

log = logging.getLogger(__name__)

def debug(*args, **kwargs):
    # to avoid overly verbose output, this is off by default
    if DEBUG_ACCESS:
        log.debug(*args, **kwargs)

def has_access(user, obj, action):
    """
    Check whether a user has the access to do action on obj.  Handles any magic
    switching based on various settings.

    Things this module understands:
    - start dates for modules
    - DISABLE_START_DATES
    - different access for staff, course staff, and students.

    user: a Django user object. May be anonymous.

    obj: The object to check access for.  For now, a module or descriptor.

    action: A string specifying the action that the client is trying to perform.

    actions depend on the obj type, but include e.g. 'enroll' for courses.  See the
    type-specific functions below for the known actions for that type.

    Returns a bool.  It is up to the caller to actually deny access in a way
    that makes sense in context.
    """
    # delegate the work to type-specific functions.
    # (start with more specific types, then get more general)
    if isinstance(obj, CourseDescriptor):
        return _has_access_course_desc(user, obj, action)

    if isinstance(obj, XModuleDescriptor):
        return _has_access_descriptor(user, obj, action)

    if isinstance(obj, XModule):
        return _has_access_xmodule(user, obj, action)

    if isinstance(obj, Location):
        return _has_access_location(user, obj, action)

    # Passing an unknown object here is a coding error, so rather than
    # returning a default, complain.
    raise TypeError("Unknown object type in has_access().  Object type: '{}'"
                    .format(type(obj)))

# ================ Implementation helpers ================================

def _has_access_course_desc(user, course, action):
    """
    Check if user has access to a course descriptor.

    Valid actions:

    'load' -- load the courseware, see inside the course
    'enroll' -- enroll.  Checks for enrollment window,
                  ACCESS_REQUIRE_STAFF_FOR_COURSE,
    'see_exists' -- can see that the course exists.
    'staff' -- staff access to course.
    """
    def can_load():
        "Can this user load this course?"
        # delegate to generic descriptor check
        return _has_access_descriptor(user, course, action)

    def can_enroll():
        """
        If the course has an enrollment period, check whether we are in it.
        (staff can always enroll)
        """

        now = time.gmtime()
        start = course.enrollment_start
        end = course.enrollment_end

        if (start is None or now > start) and (end is None or now < end):
            # in enrollment period, so any user is allowed to enroll.
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
        if settings.MITX_FEATURES.get('ACCESS_REQUIRE_STAFF_FOR_COURSE'):
            # if this feature is on, only allow courses that have ispublic set to be
            # seen by non-staff
            if course.metadata.get('ispublic'):
                return True
            return _has_staff_access_to_descriptor(user, course)

        return can_enroll() or can_load()

    checkers = {
        'load': can_load,
        'enroll': can_enroll,
        'see_exists': see_exists,
        'staff': lambda: _has_staff_access_to_descriptor(user, course)
        }

    return _dispatch(checkers, action, user, course)


def _has_access_descriptor(user, descriptor, action):
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
        # If start dates are off, can always load
        if settings.MITX_FEATURES['DISABLE_START_DATES']:
            return True

        # Check start date
        if descriptor.start is not None:
            now = time.gmtime()
            if now > descriptor.start:
                # after start date, everyone can see it
                return True
            # otherwise, need staff access
            return _has_staff_access_to_descriptor(user, descriptor)

        # No start date, so can always load.
        return True

    checkers = {
        'load': can_load,
        'staff': lambda: _has_staff_access_to_descriptor(user, descriptor)
        }

    return _dispatch(checkers, action, user, descriptor)




def _has_access_xmodule(user, xmodule, action):
    """
    Check if user has access to this xmodule.

    Valid actions:
      - same as the valid actions for xmodule.descriptor
    """
    # Delegate to the descriptor
    return has_access(user, xmodule.descriptor, action)


def _has_access_location(user, location, action):
    """
    Check if user has access to this location.

    Valid actions:
    'staff' : True if the user has staff access to this location

    NOTE: if you add other actions, make sure that

     has_access(user, location, action) == has_access(user, get_item(location), action)

    And in general, prefer checking access on loaded items, rather than locations.
    """
    checkers = {
        'staff': lambda: _has_staff_access_to_location(user, location)
        }

    return _dispatch(checkers, action, user, location)


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
              user, obj, action)
        return result

    raise ValueError("Unknown action for object type '{}': '{}'".format(
        type(obj), action))

def _course_staff_group_name(location):
    """
    Get the name of the staff group for a location.  Right now, that's staff_COURSE.

    location: something that can passed to Location.
    """
    return 'staff_%s' % Location(location).course

def _has_staff_access_to_location(user, location):
    '''
    Returns True if the given user has staff access to a location.  For now this
    is equivalent to having staff access to the course location.course.

    This means that user is in the staff_* group, or is an overall admin.

    TODO (vshnayder): this needs to be changed to allow per-course_id permissions, not per-course
    (e.g. staff in 2012 is different from 2013, but maybe some people always have access)

    course is a string: the course field of the location being accessed.
    '''
    if user is None or (not user.is_authenticated()):
        return False
    if user.is_staff:
        return True

    # If not global staff, is the user in the Auth group for this class?
    user_groups = [x[1] for x in user.groups.values_list()]
    staff_group = _course_staff_group_name(location)
    if staff_group in user_groups:
        return True
    return False

def _has_staff_access_to_course_id(user, course_id):
    """Helper method that takes a course_id instead of a course name"""
    loc = CourseDescriptor.id_to_location(course_id)
    return _has_staff_access_to_location(user, loc)


def _has_staff_access_to_descriptor(user, descriptor):
    """Helper method that checks whether the user has staff access to
    the course of the location.

    location: something that can be passed to Location
    """
    return _has_staff_access_to_location(user, descriptor.location)

