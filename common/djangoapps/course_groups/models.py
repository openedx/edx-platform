import logging

from django.contrib.auth.models import User
from django.db import models

log = logging.getLogger(__name__)

class CourseUserGroup(models.Model):
    """
    This model represents groups of users in a course.  Groups may have different types,
    which may be treated specially.  For example, a user can be in at most one cohort per
    course, and cohorts are used to split up the forums by group.
    """
    class Meta:
        unique_together = (('name', 'course_id'), )

    name = models.CharField(max_length=255,
                            help_text=("What is the name of this group?  "
                                       "Must be unique within a course."))
    users = models.ManyToManyField(User, db_index=True, related_name='course_groups',
                                   help_text="Who is in this group?")

    # Note: groups associated with particular runs of a course.  E.g. Fall 2012 and Spring
    # 2013 versions of 6.00x will have separate groups.
    course_id = models.CharField(max_length=255, db_index=True,
                                 help_text="Which course is this group associated with?")

    # For now, only have group type 'cohort', but adding a type field to support
    # things like 'question_discussion', 'friends', 'off-line-class', etc
    COHORT = 'cohort'
    GROUP_TYPE_CHOICES = ((COHORT, 'Cohort'),)
    group_type = models.CharField(max_length=20, choices=GROUP_TYPE_CHOICES)

def get_cohort(user, course_id):
    """
    Given a django User and a course_id, return the user's cohort.  In classes with
    auto-cohorting, put the user in a cohort if they aren't in one already.

    Arguments:
        user: a Django User object.
        course_id: string in the format 'org/course/run'

    Returns:
        A CourseUserGroup object if the User has a cohort, or None.
    """
    try:
        group = CourseUserGroup.objects.get(course_id=course_id,
                                            group_type=CourseUserGroup.COHORT,
                                            users__id=user.id)
    except CourseUserGroup.DoesNotExist:
        group = None

    if group:
        return group

    # TODO: add auto-cohorting logic here
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

### Helpers for cohor management views

def get_cohort_by_name(course_id, name):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.
    """
    return CourseUserGroup.objects.get(course_id=course_id,
                                       group_type=CourseUserGroup.COHORT,
                                       name=name)

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

