"""
Helper methods for Mailchimp pipeline
"""
from celery.task import task
from django.conf import settings

from openedx.adg.common.course_meta.models import CourseMeta
from student.models import CourseEnrollment

from .client import MailchimpClient


def get_active_enrollment_course_overviews_by_user(user):
    """
    Get all course overviews, for a user, for active enrollments and for running courses

    Args:
        user (user object): User model object

    Returns:
        List of course overviews
    """
    course_overviews = [
        enrollment.course
        for enrollment in CourseEnrollment.enrollments_for_user(user)
        if not enrollment.course.has_ended()
    ]
    return course_overviews


def get_active_enrollment_course_names_by_user(user):
    """
    Get comma separated course names, for all course overviews, for a user,
    for active enrollments and for running courses

    Args:
        user (user object): User model object

    Returns:
        Comma separated course names
    """
    course_overviews = get_active_enrollment_course_overviews_by_user(user)
    return ", ".join([course.display_name for course in course_overviews])


def get_active_enrollment_course_short_ids(user):
    """
    Get comma separated course short id's, for all course overviews, for a user,
    for active enrollments and for running courses

    Args:
        user (user object): User model object

    Returns:
        Comma separated course short id's
    """
    course_overviews = get_active_enrollment_course_overviews_by_user(user)
    return ", ".join([str(course.course_meta.course_short_id) for course in course_overviews])


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def send_user_info_to_mailchimp(user, created):
    """
    Add new user data to Mailchimp (audience) list

    Args:
        user (user object): User model object
        created (boolean): True if user object is created, False if user updated

    Returns:
        None
    """
    # TODO LP-2446 Add complete user info which needs to be synced with Mailchimp
    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "FULLNAME": user.get_full_name(),
            "USERNAME": user.username
        }
    }

    if created:
        user_json["merge_fields"].update({"DATEREGIS": str(user.date_joined.strftime("%m/%d/%Y"))})

    MailchimpClient().create_or_update_list_member(email=user.email, data=user_json)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def send_user_enrollments_to_mailchimp(user, course):
    """
    Update member info on Mailchimp (audience) list, related to course. Add course enrollment title
    and course short id to member contact info on Mailchimp.

    Args:
        user (user object): User model object
        course (CourseOverview): Enrolled course

    Returns:
        None
    """
    CourseMeta.objects.get_or_create(course=course)  # Create course short id for enrolled course
    enrollment_titles = get_active_enrollment_course_names_by_user(user)
    enrollment_short_ids = get_active_enrollment_course_short_ids(user)

    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "ENROLLS": enrollment_titles,
            "ENROLL_IDS": enrollment_short_ids,
        }
    }

    MailchimpClient().create_or_update_list_member(email=user.email, data=user_json)
