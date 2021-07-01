"""Celery tasks to enroll users in courses and send registration email"""

from logging import getLogger

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import DatabaseError, transaction
from edx_ace import Recipient, ace
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from student.models import CourseEnrollment

from .message_types import EnrolmentNotification
from .utils import get_org_users_qs

log = getLogger(__name__)


def get_enrolment_email_message_context(user, courses):
    """
    return context for course enrolment notification email body
    """
    site = Site.objects.get_current()
    message_context = {
        'site_name': site.domain
    }
    message_context.update(get_base_template_context(site))
    message_context.update({
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'username': user.username,
        'courses': courses,
    })
    return message_context


@task(name='send course enrolment email')
def send_course_enrolment_email(request_user_id, user_ids, course_keys_string):
    """
    send a course enrolment notification via email
    :param request_user_id: (int) request user id
    :param user_ids: (list<int>) user ids
    :param course_keys_string: (list<string>) course key
    """
    request_user = User.objects.filter(id=request_user_id).first()
    if request_user:
        for user in get_org_users_qs(request_user).filter(id__in=user_ids):
            message = EnrolmentNotification().personalize(
                recipient=Recipient(user.username, user.email),
                language='en',
                user_context=get_enrolment_email_message_context(user, course_keys_string),
            )
            ace.send(message)
    else:
        log.info("Invalid request user id - Task terminated!")


@task(name='enroll_users')
def enroll_users(request_user_id, user_ids, course_keys_string):
    """
    Enroll users in courses
    :param request_user_id: (int) request user id
    :param user_ids: (list<int>) user ids
    :param course_keys_string: (list<string>) course key
    """
    request_user = User.objects.filter(id=request_user_id).first()
    if request_user:
        enrolled_users_id = []
        all_users = get_org_users_qs(request_user).filter(id__in=user_ids)
        try:
            with transaction.atomic():
                for course_key_string in course_keys_string:
                    course_key = CourseKey.from_string(course_key_string)
                    for user in all_users:
                        CourseEnrollment.enroll(user, course_key)
                        if user.id not in enrolled_users_id:
                            enrolled_users_id.append(user.id)
            send_course_enrolment_email.delay(request_user_id, enrolled_users_id, course_keys_string)
            log.info("Enrolled user(s): {}".format(enrolled_users_id))
        except DatabaseError:
            log.info("Task terminated!")
    else:
        log.info("Invalid request user id - Task terminated!")
