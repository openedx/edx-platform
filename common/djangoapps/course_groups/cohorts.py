"""
This file contains the logic for cohort groups, as exposed internally to the
forums, and to the cohort admin views.
"""

from django.contrib.auth.models import User
import logging

from courseware import courses
from .models import CourseUserGroup

log = logging.getLogger(__name__)

def is_course_cohorted(course_id):
    """
    Given a course id, return a boolean for whether or not the course is
    cohorted.

    Raises:
       Http404 if the course doesn't exist.
    """
    return courses.get_course_by_id(course_id).is_cohorted


def get_cohort_id(user, course_id):
    """
    Given a course id and a user, return the id of the cohort that user is
    assigned to in that course.  If they don't have a cohort, return None.
    """
    cohort = get_cohort(user, course_id)
    return None if cohort is None else cohort.id


def is_commentable_cohorted(course_id, commentable_id):
    """
    Given a course and a commentable id, return whether or not this commentable
    is cohorted.

    Raises:
        Http404 if the course doesn't exist.
    """
    course = courses.get_course_by_id(course_id)
    ans = commentable_id in course.cohorted_discussions()
    log.debug("is_commentable_cohorted({0}, {1}) = {2}".format(course_id,
                                                               commentable_id,
                                                               ans))
    return ans


def get_cohort(user, course_id):
    c = _get_cohort(user, course_id)
    log.debug("get_cohort({0}, {1}) = {2}".format(user, course_id, c.id))

def _get_cohort(user, course_id):
    """
    Given a django User and a course_id, return the user's cohort.  In classes with
    auto-cohorting, put the user in a cohort if they aren't in one already.

    Arguments:
        user: a Django User object.
        course_id: string in the format 'org/course/run'

    Returns:
        A CourseUserGroup object if the User has a cohort, or None.

    Raises:
       ValueError if the course_id doesn't exist.
    """
    # First check whether the course is cohorted (users shouldn't be in a cohort
    # in non-cohorted courses, but settings can change after )
    try:
        course = courses.get_course_by_id(course_id)
    except Http404:
        raise ValueError("Invalid course_id")

    if not course.is_cohorted:
        return None

    try:
        group = CourseUserGroup.objects.get(course_id=course_id,
                                            group_type=CourseUserGroup.COHORT,
                                            users__id=user.id)
    except CourseUserGroup.DoesNotExist:
        group = None

    if group:
        return group

    # TODO: add auto-cohorting logic here once we know what that will be.
    return None


def get_course_cohorts(course_id):
    """
    Get a list of all the cohorts in the given course.

    Arguments:
        course_id: string in the format 'org/course/run'

    Returns:
        A list of CourseUserGroup objects.  Empty if there are no cohorts.
    """
    return list(CourseUserGroup.objects.filter(course_id=course_id,
                                               group_type=CourseUserGroup.COHORT))

### Helpers for cohort management views

def get_cohort_by_name(course_id, name):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.
    """
    return CourseUserGroup.objects.get(course_id=course_id,
                                       group_type=CourseUserGroup.COHORT,
                                       name=name)

def get_cohort_by_id(course_id, cohort_id):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.  Uses the course_id for extra validation...
    """
    return CourseUserGroup.objects.get(course_id=course_id,
                                       group_type=CourseUserGroup.COHORT,
                                       id=cohort_id)

def add_cohort(course_id, name):
    """
    Add a cohort to a course.  Raises ValueError if a cohort of the same name already
    exists.
    """
    log.debug("Adding cohort %s to %s", name, course_id)
    if CourseUserGroup.objects.filter(course_id=course_id,
                                      group_type=CourseUserGroup.COHORT,
                                      name=name).exists():
        raise ValueError("Can't create two cohorts with the same name")

    return CourseUserGroup.objects.create(course_id=course_id,
                                          group_type=CourseUserGroup.COHORT,
                                          name=name)

class CohortConflict(Exception):
    """
    Raised when user to be added is already in another cohort in same course.
    """
    pass

def add_user_to_cohort(cohort, username_or_email):
    """
    Look up the given user, and if successful, add them to the specified cohort.

    Arguments:
        cohort: CourseUserGroup
        username_or_email: string.  Treated as email if has '@'

    Returns:
        User object.

    Raises:
        User.DoesNotExist if can't find user.

        ValueError if user already present in this cohort.

        CohortConflict if user already in another cohort.
    """
    if '@' in username_or_email:
        user = User.objects.get(email=username_or_email)
    else:
        user = User.objects.get(username=username_or_email)

    # If user in any cohorts in this course already, complain
    course_cohorts = CourseUserGroup.objects.filter(
        course_id=cohort.course_id,
        users__id=user.id,
        group_type=CourseUserGroup.COHORT)
    if course_cohorts.exists():
        if course_cohorts[0] == cohort:
            raise ValueError("User {0} already present in cohort {1}".format(
                user.username,
                cohort.name))
        else:
            raise CohortConflict("User {0} is in another cohort {1} in course"
                                 .format(user.username,
                                         course_cohorts[0].name))

    cohort.users.add(user)
    return user


def get_course_cohort_names(course_id):
    """
    Return a list of the cohort names in a course.
    """
    return [c.name for c in get_course_cohorts(course_id)]


def delete_empty_cohort(course_id, name):
    """
    Remove an empty cohort.  Raise ValueError if cohort is not empty.
    """
    cohort = get_cohort_by_name(course_id, name)
    if cohort.users.exists():
        raise ValueError(
            "Can't delete non-empty cohort {0} in course {1}".format(
                name, course_id))

    cohort.delete()

