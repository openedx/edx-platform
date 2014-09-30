"""
This file contains the logic for cohort groups, as exposed internally to the
forums, and to the cohort admin views.
"""

import logging
import random

from django.http import Http404
from django.utils.translation import ugettext as _

from courseware import courses
from student.models import get_user_by_username_or_email
from .models import CourseUserGroup

log = logging.getLogger(__name__)


# A 'default cohort' is an auto-cohort that is automatically created for a course if no auto_cohort_groups have been
# specified. It is intended to be used in a cohorted-course for users who have yet to be assigned to a cohort.
# Note 1: If an administrator chooses to configure a cohort with the same name, the said cohort will be used as
#         the "default cohort".
# Note 2: If auto_cohort_groups are configured after the 'default cohort' has been created and populated, the
#         stagnant 'default cohort' will still remain (now as a manual cohort) with its previously assigned students.
# Translation Note: We are NOT translating this string since it is the constant identifier for the "default group"
#                   and needed across product boundaries.
DEFAULT_COHORT_NAME = "Default Group"


class CohortAssignmentType(object):
    """
    The various types of rule-based cohorts
    """
    # No automatic rules are applied to this cohort; users must be manually added.
    NONE = "none"

    # One of (possibly) multiple cohort groups to which users are randomly assigned.
    # Note: The 'default cohort' group is included in this category iff it exists and
    # there are no other random groups. (Also see Note 2 above.)
    RANDOM = "random"

    @staticmethod
    def get(cohort, course):
        """
        Returns the assignment type of the given cohort for the given course
        """
        if cohort.name in course.auto_cohort_groups:
            return CohortAssignmentType.RANDOM
        elif len(course.auto_cohort_groups) == 0 and cohort.name == DEFAULT_COHORT_NAME:
            return CohortAssignmentType.RANDOM
        else:
            return CohortAssignmentType.NONE


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


def get_cohort_id(user, course_key):
    """
    Given a course key and a user, return the id of the cohort that user is
    assigned to in that course.  If they don't have a cohort, return None.
    """
    cohort = get_cohort(user, course_key)
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
    Given a course_key return a set of strings representing cohorted commentables.
    """

    course = courses.get_course_by_id(course_key)

    if not course.is_cohorted:
        # this is the easy case :)
        ans = set()
    else:
        ans = course.cohorted_discussions

    return ans


def get_cohort(user, course_key):
    """
    Given a Django user and a CourseKey, return the user's cohort in that
    cohort.

    Arguments:
        user: a Django User object.
        course_key: CourseKey

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
        return None

    try:
        return CourseUserGroup.objects.get(course_id=course_key,
                                            group_type=CourseUserGroup.COHORT,
                                            users__id=user.id)
    except CourseUserGroup.DoesNotExist:
        # Didn't find the group.  We'll go on to create one if needed.
        pass

    choices = course.auto_cohort_groups
    if len(choices) > 0:
        # Randomly choose one of the auto_cohort_groups, creating it if needed.
        group_name = local_random().choice(choices)
    else:
        # Use the "default cohort".
        group_name = DEFAULT_COHORT_NAME

    group, __ = CourseUserGroup.objects.get_or_create(
        course_id=course_key,
        group_type=CourseUserGroup.COHORT,
        name=group_name
    )
    user.course_groups.add(group)
    return group


def get_course_cohorts(course):
    """
    Get a list of all the cohorts in the given course. This will include auto cohorts,
    regardless of whether or not the auto cohorts include any users.

    Arguments:
        course: the course for which cohorts should be returned

    Returns:
        A list of CourseUserGroup objects.  Empty if there are no cohorts. Does
        not check whether the course is cohorted.
    """
    # Ensure all auto cohorts are created.
    for group_name in course.auto_cohort_groups:
        CourseUserGroup.objects.get_or_create(
            course_id=course.location.course_key,
            group_type=CourseUserGroup.COHORT,
            name=group_name
        )

    return list(CourseUserGroup.objects.filter(
        course_id=course.location.course_key,
        group_type=CourseUserGroup.COHORT
    ))

### Helpers for cohort management views


def get_cohort_by_name(course_key, name):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.
    """
    return CourseUserGroup.objects.get(
        course_id=course_key,
        group_type=CourseUserGroup.COHORT,
        name=name
    )


def get_cohort_by_id(course_key, cohort_id):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.  Uses the course_key for extra validation...
    """
    return CourseUserGroup.objects.get(
        course_id=course_key,
        group_type=CourseUserGroup.COHORT,
        id=cohort_id
    )


def add_cohort(course_key, name):
    """
    Add a cohort to a course.  Raises ValueError if a cohort of the same name already
    exists.
    """
    log.debug("Adding cohort %s to %s", name, course_key)
    if CourseUserGroup.objects.filter(course_id=course_key,
                                      group_type=CourseUserGroup.COHORT,
                                      name=name).exists():
        raise ValueError(_("You cannot create two cohorts with the same name"))

    try:
        course = courses.get_course_by_id(course_key)
    except Http404:
        raise ValueError("Invalid course_key")

    return CourseUserGroup.objects.create(
        course_id=course.id,
        group_type=CourseUserGroup.COHORT,
        name=name
    )


def add_user_to_cohort(cohort, username_or_email):
    """
    Look up the given user, and if successful, add them to the specified cohort.

    Arguments:
        cohort: CourseUserGroup
        username_or_email: string.  Treated as email if has '@'

    Returns:
        Tuple of User object and string (or None) indicating previous cohort

    Raises:
        User.DoesNotExist if can't find user.
        ValueError if user already present in this cohort.
    """
    user = get_user_by_username_or_email(username_or_email)
    previous_cohort = None

    course_cohorts = CourseUserGroup.objects.filter(
        course_id=cohort.course_id,
        users__id=user.id,
        group_type=CourseUserGroup.COHORT
    )
    if course_cohorts.exists():
        if course_cohorts[0] == cohort:
            raise ValueError("User {user_name} already present in cohort {cohort_name}".format(
                user_name=user.username,
                cohort_name=cohort.name
            ))
        else:
            previous_cohort = course_cohorts[0].name
            course_cohorts[0].users.remove(user)

    cohort.users.add(user)
    return (user, previous_cohort)
