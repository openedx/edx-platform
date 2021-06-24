"""Celery tasks for to update user progress and send reminder emails"""

from logging import getLogger

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import IntegrityError
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from edx_ace import ace
from edx_ace.recipient import Recipient
from six import text_type

from grades.api import CourseGradeFactory
from openedx.core.djangoapps.ace_common.template_context import get_base_template_context
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.features.pakx.lms.overrides.message_types import CourseProgress
from openedx.features.pakx.lms.overrides.models import CourseProgressStats
from openedx.features.pakx.lms.overrides.utils import (
    create_dummy_request,
    get_course_progress_percentage,
    get_date_diff_in_days
)
from student.models import CourseEnrollment

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
        'completed': data.get('completed'),
        'status_message': data.get('status_message')
    })

    return message_context


@task(name='send_reminder_email')
def send_reminder_email(data, course_key):
    """
    A task to send reminder emails
    :param data: (dict) dict containing data for the email
    :param course_key: (CourseKey)
    """

    log.info("Sending course email to :{}, for:{}, progress:{}, complete:{}".format(
        data.get("email"), data.get("course_name"), data.get("course_progress"), data.get("completed")))
    site = Site.objects.get_current()
    course_url = '{url}{path}'.format(
        url=site.domain.strip(),
        path=reverse('course_root', kwargs={'course_id': course_key})
    )
    data['course_url'] = course_url
    message_context = _get_email_message_context(data)
    user = User.objects.get(username=data.get('username'), email=data.get('email'))
    log.info("**** user:{} message_context:{}".format(user, message_context))
    with emulate_http_request(site, user):
        msg = CourseProgress().personalize(
            recipient=Recipient(data.get('username'), data.get('email')),
            language=data.get('language'),
            user_context=message_context
        )
        ace.send(msg)


@task(name='add_enrollment_record')
def add_enrollment_record(user_id, course_id):
    """
    Add current enrollment record
    :param user_id: (str) user id
    :param course_id: (CourseKeyField) course key
    """

    try:
        CourseProgressStats.objects.create(user_id=user_id, course_id=course_id, grade=0)
    except IntegrityError:
        log.info("Enrollment record for {} & User:{} already registered".format(course_id, user_id))


@task(name='remove_enrollment_record')
def remove_enrollment_record(user_id, course_id):
    """
    Remove current enrollment record
    :param user_id: (str) user name
    :param course_id: (CourseKeyField) course key
    """

    CourseProgressStats.objects.filter(user_id=user_id, course_id=course_id).delete()


@task(name='copy_active_course_enrollments')
def copy_active_course_enrollments():
    """
    A task that copies active enrollments to CourseProgressStats model
    """
    active_enrollments = CourseEnrollment.objects.filter(is_active=True)
    log.info("Found {} active enrollment records, ".format(len(active_enrollments)))
    for enrollment in active_enrollments:
        add_enrollment_record(enrollment.user.id, enrollment.course.id)


@task(name='update_course_progress_stats')
def update_course_progress_stats():
    """
    A task that checks all the current progress models & sends course completion or reminder emails
    """

    email_status_to_filter = [CourseProgressStats.NO_EMAIL_SENT, CourseProgressStats.REMINDER_SENT]
    progress_models = CourseProgressStats.objects.filter(
        Q(email_reminder_status__in=email_status_to_filter) | Q(progress__lt=100)
    )
    log.info("Fetching records, found {} active models".format(len(progress_models)))
    for item in progress_models:
        course_progress = float(
            get_course_progress_percentage(create_dummy_request(Site.objects.get_current(), item.user),
                                           text_type(item.course_id)))
        course_overview = CourseOverview.get_from_id(item.course_id)
        grades = CourseGradeFactory().read(user=item.user, course_key=item.course_id)
        completed = grades.passed and course_progress >= 100
        fields_list = ['progress', 'grade']
        if course_progress >= 100:
            item.completion_date = timezone.now()
            fields_list.append('completion_date')
        item.progress = course_progress
        item.grade = grades.letter_grade

        data = {'course_name': course_overview.display_name, 'username': item.user.username, 'email': item.user.email,
                'language': get_user_preference(item.user, LANGUAGE_KEY),
                'completed': completed,
                'status_message': "Completed" if completed else "Pending",
                'course_progress': course_progress}

        if data["completed"] and item.email_reminder_status != CourseProgressStats.COURSE_COMPLETED:
            send_reminder_email.delay(data, text_type(item.course_id))
            item.email_reminder_status = CourseProgressStats.COURSE_COMPLETED
            fields_list.append('email_reminder_status')
        elif course_overview.end_date:
            remaining_days = get_date_diff_in_days(course_overview.end_date)
            if remaining_days <= settings.COURSE_PROGRESS_REMINDER_EMAIL_DAYS and item.email_reminder_status == 0:
                send_reminder_email.delay(data, text_type(item.course_id))
                item.email_reminder_status = CourseProgressStats.REMINDER_SENT
                fields_list.append('email_reminder_status')
        item.save(update_fields=fields_list)
