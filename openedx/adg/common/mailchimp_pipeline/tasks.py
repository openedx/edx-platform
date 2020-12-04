"""
Tasks for Mailchimp pipeline
"""
import logging

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User

from openedx.adg.common.course_meta.models import CourseMeta
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import UserProfile

from .client import MailchimpClient
from .helpers import get_enrollment_course_names_and_short_ids_by_user

log = logging.getLogger(__name__)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_user_info_to_mailchimp(sender, instance):
    """
    Sync user data to Mailchimp (audience) list

    Args:
        sender (obj): User related model class which is updated or created.
        instance (obj): Object of the sender class which is updated or created.

    Returns:
        None
    """
    user_email = instance.email if sender == User else instance.user.email
    user_json = {
        'email_address': user_email,
        'status_if_new': 'subscribed',
        'merge_fields': {}
    }

    if sender == User:
        user_json['merge_fields'].update(
            {
                'USERNAME': instance.username,
                'DATEREGIS': str(instance.date_joined.strftime('%m/%d/%Y'))
            }
        )
    elif sender == UserProfile:
        user_json['merge_fields'].update(
            {
                'LOCATION': instance.city,
                'FULLNAME': instance.name
            }
        )
    elif sender == UserApplication:
        user_json['merge_fields'].update(
            {
                'ORG_NAME': instance.organization or '',
                'APP_STATUS': instance.status,
                'B_LINE': instance.business_line.title or ''
            }
        )
    elif sender == ExtendedUserProfile:
        user_json['merge_fields'].update(
            {
                'COMPANY': instance.company.title or ''
            }
        )

    MailchimpClient().create_or_update_list_member(email=user_email, data=user_json)


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
