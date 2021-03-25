from celery import task
from six import text_type
from logging import getLogger
from django.urls import reverse
from django.conf import settings
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from edx_ace import ace
from edx_ace.recipient import Recipient
from grades.api import CourseGradeFactory
from student.models import CourseEnrollment
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.pakx.lms.overrides.utils import get_date_diff_in_days
from openedx.features.pakx.lms.overrides.message_types import CourseProgress
from openedx.features.pakx.lms.overrides.models import CourseProgressEmailModel
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context

log = getLogger(__name__)


def _get_email_message_context(data):
    """
    get basic context for email

    :returns: (dict) a dict object
    """

    site = Site.objects.get_current()
    message_context = get_base_template_context(site)
    message_context.update({
        'platform_name': configuration_helpers.get_value('PLATFORM_NAME', settings.PLATFORM_NAME),
        'course_name': data.get('course_name'),
        'status': data.get('status')
    })

    return message_context


@task(name='send_reminder_email')
def send_reminder_email(data, course_key):
    """
    A task to send reminder emails
    :param data: (dict) dict containing data for the email
    :param course_key: (CourseKey)
    """

    site = Site.objects.get_current()
    course_url = '{url}{path}'.format(
        url=site.domain.strip(),
        path=reverse('course_root', kwargs={'course_id': course_key})
    )
    data['course_url'] = course_url
    message_context = _get_email_message_context(data)
    user = User.objects.get(username=data.get('username'), email=data.get('email'))
    with emulate_http_request(site, user):
        msg = CourseProgress().personalize(
            recipient=Recipient(data.get('username'), data.get('email')),
            language=data.get('language'),
            user_context=message_context
        )
        ace.send(msg)


@task(name='add_enrollment_record')
def add_enrollment_record(user, course_id):
    """
    Add current enrollment record
    :param user: (settings.User) user object
    :param course_id: (CourseKeyField) course key
    """

    try:
        CourseProgressEmailModel.objects.create(user=user, course_id=course_id)
    except IntegrityError:
        log.info("Enrollment record for {} & User:{} already registered".format(course_id, user))


@task(name='remove_enrollment_record')
def remove_enrollment_record(user, course_id):
    """
    Remove current enrollment record
    :param user: (settings.User) user object
    :param course_id: (CourseKeyField) course key
    """

    record = CourseProgressEmailModel.objects.filter(user=user, course_id=course_id)
    if record:
        record.delete()


@task(name='copy_active_course_enrollments')
def copy_active_course_enrollments():
    """
    A task that copies active enrollments to CourseProgressEmailModel model
    """
    active_enrollments = CourseEnrollment.objects.filter(is_active=True)
    log.info("Found {} active enrollment records, ".format(len(active_enrollments)))
    for enrollment in active_enrollments:
        add_enrollment_record(enrollment.user, enrollment.course.id)


@task(name='send_course_completion_email')
def check_and_send_email_to_course_learners():
    """
    A task that checks all the current progress models & sends course completion or reminder emails
    """
    progress_models = CourseProgressEmailModel.objects.filter(status__in=[0, 1])
    log.info("Fetching records, found {} active models".format(len(progress_models)))
    for item in progress_models:
        course_overview = CourseOverview.get_from_id(item.course_id)
        grades = CourseGradeFactory().read(user=item.user, course_key=item.course_id)
        data = {'course_name': course_overview.display_name,
                'username': item.user.username, 'email': item.user.email,
                'language': get_user_preference(item.user, LANGUAGE_KEY),
                'status': grades.percent >= 1.0,
                'status_message': "Completed" if grades.percent >= 0 else "Pending"}
        if grades.percent >= 1.0:
            log.info("Sending course completion email to :{}, for:{}".format(data.get("email"),
                                                                             data.get("course_name")))
            send_reminder_email.delay(data, text_type(item.course_id))
            item.status = 2
            item.save()
        elif course_overview.end_date:
            remaining_days = get_date_diff_in_days(course_overview.end_date)
            if remaining_days <= 10 and item.status == 0:
                log.info("Sending course reminder email to :{}, for:{}".format(data.get("email"),
                                                                               data.get("course_name")))
                send_reminder_email.delay(data, text_type(item.course_id))
                item.status = 1
                item.save()

