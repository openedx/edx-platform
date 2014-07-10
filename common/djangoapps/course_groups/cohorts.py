"""
This file contains the logic for cohort groups, as exposed internally to the
forums, and to the cohort admin views.
"""

from django.http import Http404
import logging
import random

from courseware import courses
from student.models import get_user_by_username_or_email
from .models import CourseUserGroup

log = logging.getLogger(__name__)


# tl;dr: global state is bad.  capa reseeds random every time a problem is loaded.  Even
# if and when that's fixed, it's a good idea to have a local generator to avoid any other
# code that messes with the global random module.
_local_random = None

def local_random():
    """
    Get the local random number generator.  In a function so that we don't run
    random.Random() at import time.
    """
    # ironic, isn't it?
    global _local_random

    if _local_random is None:
        _local_random = random.Random()

    return _local_random


def is_course_cohorted(course_key):
    """
    Given a course key, return a boolean for whether or not the course is
    cohorted.

    Raises:
       Http404 if the course doesn't exist.
    """
    return courses.get_course_by_id(course_key).is_cohorted


def get_cohort_id(user, course_key, group_type=CourseUserGroup.COHORT):
    """
    Given a course key and a user, return the id of the cohort that user is
    assigned to in that course.  If they don't have a cohort, return None.
    """
    cohort = get_cohort(user, course_key, group_type=group_type)
    return None if cohort is None else cohort.id


def is_commentable_cohorted(course_key, commentable_id):
    """
    Args:
        course_key: CourseKey
        commentable_id: string

    Returns:
        Bool: is this commentable cohorted?

    Raises:
        Http404 if the course doesn't exist.
    """
    course = courses.get_course_by_id(course_key)

    if not course.is_cohorted:
        # this is the easy case :)
        ans = False
    elif commentable_id in course.top_level_discussion_topic_ids:
        # top level discussions have to be manually configured as cohorted
        # (default is not)
        ans = commentable_id in course.cohorted_discussions
    else:
        # inline discussions are cohorted by default
        ans = True

    log.debug(u"is_commentable_cohorted({0}, {1}) = {2}".format(
        course_key, commentable_id, ans
    ))
    return ans


def get_cohorted_commentables(course_key):
    """
    Given a course_key return a list of strings representing cohorted commentables
    """

    course = courses.get_course_by_id(course_key)

    if not course.is_cohorted:
        # this is the easy case :)
        ans = []
    else:
        ans = course.cohorted_discussions

    return ans


def get_cohort(user, course_key, group_type=CourseUserGroup.COHORT, allow_multiple=False):
    """
    Given a django User and a CourseKey, return the user's cohort in that
    cohort.

    Arguments:
        user: a Django User object.
        course_key: CourseKey
        group_type: cohort type to query.

    Returns:
        A CourseUserGroup object if the course is cohorted and the User has a
        cohort, else None.

    Raises:
       ValueError if the CourseKey doesn't exist.
    """
    # First check whether the course is cohorted (users shouldn't be in a cohort
    # in non-cohorted courses, but settings can change after course starts)
    try:
        course = courses.get_course_by_id(course_key)
    except Http404:
        raise ValueError("Invalid course_key")

    if not course.is_cohorted:
        return None if not allow_multiple else []

    params = {'course_id': course_key,
              'users__id': user.id}
    if group_type != CourseUserGroup.ANY:
        params['group_type'] = group_type

    if allow_multiple:
        return list(CourseUserGroup.objects.filter(**params))

    try:
        return CourseUserGroup.objects.get(**params)
    except CourseUserGroup.DoesNotExist:
        # Didn't find the group.  We'll go on to create one if needed.
        pass

    if not course.auto_cohort:
        return None

    if group_type != CourseUserGroup.COHORT:
        log.warning("auto_cohort is only supported with course group of 'COHORT' type")
        return None

    choices = course.auto_cohort_groups
    n = len(choices)
    if n == 0:
        # Nowhere to put user
        log.warning("Course %s is auto-cohorted, but there are no"
                    " auto_cohort_groups specified",
                    course_key)
        return None

    # Put user in a random group, creating it if needed
    group_name = local_random().choice(choices)

    group, created = CourseUserGroup.objects.get_or_create(
        course_id=course_key,
        group_type=group_type,
        name=group_name
    )

    user.course_groups.add(group)
    return group


def get_course_cohorts(course_key, group_type=CourseUserGroup.COHORT):
    """
    Get a list of all the cohorts in the given course.

    Arguments:
        course_key: CourseKey
        group_type: cohort type to query.

    Returns:
        A list of CourseUserGroup objects.  Empty if there are no cohorts. Does
        not check whether the course is cohorted.
    """
    params = {'course_id': course_key}
    if group_type != CourseUserGroup.ANY:
        params['group_type'] = group_type

    return list(CourseUserGroup.objects.filter(**params))

### Helpers for cohort management views


def get_cohort_by_name(course_key, name, group_type=CourseUserGroup.COHORT):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.
    """
    if group_type == CourseUserGroup.ANY:
        raise ValueError("invalid group_type for get_cohort_by_name")

    return CourseUserGroup.objects.get(course_id=course_key,
                                       group_type=group_type,
                                       name=name)


def get_cohort_by_id(course_key, cohort_id):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.  Uses the course_key for extra validation...
    """
    return CourseUserGroup.objects.get(course_id=course_key, id=cohort_id)


def add_cohort(course_key, name, group_type=CourseUserGroup.COHORT):
    """
    Add a cohort to a course.  Raises ValueError if a cohort of the same name already
    exists.
    """
    log.debug("Adding cohort %s to %s", name, course_key)
    if CourseUserGroup.objects.filter(course_id=course_key,
                                      group_type=group_type,
                                      name=name).exists():
        raise ValueError("Can't create two cohorts with the same name")

    return CourseUserGroup.objects.create(course_id=course_key,
                                          group_type=group_type,
                                          name=name)


class CohortConflict(Exception):
    """
    Raised when user to be added is already in another cohort in same course.
    """
    pass


def add_user_to_cohort(cohort, username_or_email, group_type=CourseUserGroup.COHORT, allow_multiple=False):
    """
    Look up the given user, and if successful, add them to the specified cohort.

    Arguments:
        cohort: CourseUserGroup
        username_or_email: string.  Treated as email if has '@'
        group_type: cohort type to query
        allow_multiple: specify if the user can be in multiple cohorts

    Returns:
        Tuple of User object and string (or None) indicating previous cohort

    Raises:
        User.DoesNotExist if can't find user.

        ValueError if user already present in this cohort.
    """
    user = get_user_by_username_or_email(username_or_email)
    previous_cohort = None

    if not allow_multiple:
        course_cohorts = CourseUserGroup.objects.filter(
            course_id=cohort.course_id,
            users__id=user.id,
            group_type=group_type)
        if course_cohorts.exists():
            if course_cohorts[0] == cohort:
                raise ValueError("User {0} already present in cohort {1}".format(
                    user.username,
                    cohort.name))
            else:
                previous_cohort = course_cohorts[0].name
                course_cohorts[0].users.remove(user)

    cohort.users.add(user)
    return (user, previous_cohort)


def remove_user_from_cohort(cohort, username_or_email, group_type=CourseUserGroup.COHORT):
    """
    Look up the given user, and if successful, remove them to the specified cohort.

    Arguments:
        cohort: CourseUserGroup
        username_or_email: string.  Treated as email if has '@'
        group_type: cohort type to query

    Returns:
        User object that has been removed from the cohort

    Raises:
        User.DoesNotExist if can't find user.

        ValueError if user is not in this cohort.
    """

    if group_type == CourseUserGroup.ANY:
        raise ValueError("Invalid group_type for remove_user_from_cohort.")

    user = get_user_by_username_or_email(username_or_email)

    course_cohorts = CourseUserGroup.objects.filter(
        course_id=cohort.course_id,
        users__id=user.id,
        group_type=group_type,
    )
    if not course_cohorts.exists():
        raise ValueError("User {0} is not in cohort {1}".format(
            user.username,
            cohort.name))

    cohort.users.remove(user)
    return user

def get_course_cohort_names(course_key, group_type=CourseUserGroup.COHORT):
    """
    Return a list of the cohort names in a course.
    """
    return [c.name for c in get_course_cohorts(course_key, group_type=group_type)]


def delete_empty_cohort(course_key, name, group_type=CourseUserGroup.COHORT):
    """
    Remove an empty cohort.  Raise ValueError if cohort is not empty.
    """
    cohort = get_cohort_by_name(course_key, name, group_type=group_type)
    if cohort.users.exists():
        raise ValueError(
            "Can't delete non-empty cohort {0} in course {1}".format(
                name, course_key))

    cohort.delete()
