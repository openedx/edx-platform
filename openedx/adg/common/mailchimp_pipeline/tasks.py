"""
Tasks for Mailchimp pipeline
"""
import logging

from celery.task import task
from django.conf import settings

from openedx.adg.common.course_meta.models import CourseMeta
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .client import MailchimpClient
from .helpers import get_enrollment_course_names_and_short_ids_by_user

log = logging.getLogger(__name__)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_user_info_to_mailchimp(instance, **kwargs):  # pylint: disable=unused-argument
    """
    Add new user data to Mailchimp (audience) list

    Args:
        instance (User): The user object

    Returns:
        None
    """
    # TODO LP-2446 Add complete user info which needs to be synced with Mailchimp
    user_json = {
        "email_address": instance.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "FULLNAME": instance.get_full_name(),
            "USERNAME": instance.username
        }
    }

    user_json["merge_fields"].update({"DATEREGIS": str(instance.date_joined.strftime("%m/%d/%Y"))})

    MailchimpClient().create_or_update_list_member(email=instance.email, data=user_json)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_user_enrollments_to_mailchimp(user, course_id, **kwargs):  # pylint: disable=unused-argument
    """
    Update member info on Mailchimp (audience) list, related to course. Add course enrollment title
    and course short id to member contact info on Mailchimp.

    Args:
        user (user object): User model object
        course_id (CourseKeyField): Enrolled course id

    Returns:
        None
    """
    try:
        course = CourseOverview.objects.get(id=course_id)
    except CourseOverview.DoesNotExist:
        log.error(
            'Unable to sync course enrollment to mailchimp, for course={course_id}'.format(course_id=course_id)
        )
        return

    CourseMeta.objects.get_or_create(course=course)  # Create course short id for enrolled course
    enrollment_short_ids, enrollment_titles = get_enrollment_course_names_and_short_ids_by_user(user)

    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "ENROLLS": enrollment_titles,
            "ENROLL_IDS": enrollment_short_ids,
        }
    }

    MailchimpClient().create_or_update_list_member(email=user.email, data=user_json)
