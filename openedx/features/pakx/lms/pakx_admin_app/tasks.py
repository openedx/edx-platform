"""Celery tasks to enroll users in courses and send registration email"""

from datetime import datetime
from logging import getLogger

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import DatabaseError, transaction
from edx_ace import Recipient, ace
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.celery.task_utils import emulate_http_request
from student.models import CourseEnrollment

from .message_types import EnrolmentNotification
from .utils import get_org_users_qs

log = getLogger(__name__)


def get_enrolment_email_message_context(site, user, course, url, image_url):
    """
    return context for course enrolment notification email body
    """
    dashboard_url = 'https://' + site.domain + '/dashboard'
    message_context = {
        'site_name': site.domain
    }
    message_context.update(get_base_template_context(site, user=user))
    message_context.update({
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'date': datetime.today().strftime("%A, %B %d, %Y"),
        'username': user.profile.name or user.username,
        'dashboard_url': dashboard_url,
        'course': course,
        'url': url,
        'image_url': image_url
    })
    return message_context


@task(name='send course enrolment email')
def send_course_enrolment_email(request_user_id, user_ids, courses_map):
    """
    send a course enrolment notification via email
    :param request_user_id: (int) request user id
    :param user_ids: (list<int>) user ids
    :param courses_map: (list<dict>) contains dict with course_display_name, course_url, course_image_url
    """
    site = Site.objects.get_current()
    request_user = User.objects.filter(id=request_user_id).first()
    if request_user:
        for user in get_org_users_qs(request_user).filter(id__in=user_ids):
            for course_map in courses_map:
                with emulate_http_request(site, user):
                    user_context = get_enrolment_email_message_context(
                        site, user, course_map["display_name"], course_map["url"], course_map["image_url"]
                    )
                    message = EnrolmentNotification().personalize(
                        recipient=Recipient(user.username, user.email),
                        language='en',
                        user_context=user_context,
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
        courses_map = []
        all_users = get_org_users_qs(request_user).filter(id__in=user_ids)
        absolute_domain = 'https://' + Site.objects.get_current().domain
        course_url_template = "{domain}/courses/{course_id}/overview"
        try:
            with transaction.atomic():
                for course_key_string in course_keys_string:
                    course_key = CourseKey.from_string(course_key_string)
                    course_overview = CourseOverview.objects.get(id=CourseKey.from_string(course_key_string))
                    courses_map.append({
                        'display_name': course_overview.display_name,
                        'url': course_url_template.format(domain=absolute_domain, course_id=course_key_string),
                        'image_url': absolute_domain + course_overview.course_image_url
                    })
                    for user in all_users:
                        try:
                            CourseEnrollment.enroll(user, course_key, check_access=True)
                            enrolled_users_id.append(user.id)
                        except Exception:  # pylint: disable=broad-except
                            pass
            send_course_enrolment_email.delay(request_user_id, enrolled_users_id, courses_map)
            log.info("Enrolled user(s): {}".format(enrolled_users_id))
        except DatabaseError:
            log.info("Task terminated!")
    else:
        log.info("Invalid request user id - Task terminated!")
