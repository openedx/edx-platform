import datetime
from itertools import groupby
from logging import getLogger
from urlparse import urlparse

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Min
from django.db.utils import DatabaseError
from django.utils.http import urlquote
from edx_ace import ace
from edx_ace.message import Message, MessageType
from edx_ace.recipient import Recipient
from edx_ace.utils.date import deserialize
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import marketing_link
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig

log = getLogger(__name__)


ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)
KNOWN_RETRY_ERRORS = (  # Errors we expect occasionally that could resolve on retry
    DatabaseError,
    ValidationError,
)


@task(bind=True, default_retry_delay=30, routing_key=ROUTING_KEY)
def update_course_schedules(self, **kwargs):
    course_key = CourseKey.from_string(kwargs['course_id'])
    new_start_date = deserialize(kwargs['new_start_date_str'])
    new_upgrade_deadline = deserialize(kwargs['new_upgrade_deadline_str'])

    try:
        Schedule.objects.filter(enrollment__course_id=course_key).update(
            start=new_start_date,
            upgrade_deadline=new_upgrade_deadline
        )
    except Exception as exc:  # pylint: disable=broad-except
        if not isinstance(exc, KNOWN_RETRY_ERRORS):
            log.exception("Unexpected failure: task id: %s, kwargs=%s".format(self.request.id, kwargs))
        raise self.retry(kwargs=kwargs, exc=exc)


class RecurringNudge(MessageType):
    def __init__(self, day, *args, **kwargs):
        super(RecurringNudge, self).__init__(*args, **kwargs)
        self.name = "recurringnudge_day{}".format(day)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def recurring_nudge_schedule_hour(
    site_id, day, target_hour_str, org_list, exclude_orgs=False, override_recipient_email=None,
):
    target_hour = deserialize(target_hour_str)
    msg_type = RecurringNudge(day)

    for (user, language, context) in _recurring_nudge_schedules_for_hour(target_hour, org_list, exclude_orgs):
        msg = msg_type.personalize(
            Recipient(
                user.username,
                override_recipient_email or user.email,
            ),
            language,
            context,
        )
        _recurring_nudge_schedule_send.apply_async((site_id, str(msg)), retry=False)


@task(ignore_result=True, routing_key=ROUTING_KEY)
def _recurring_nudge_schedule_send(site_id, msg_str):
    site = Site.objects.get(pk=site_id)
    if not ScheduleConfig.current(site).deliver_recurring_nudge:
        return

    msg = Message.from_string(msg_str)
    ace.send(msg)


def _recurring_nudge_schedules_for_hour(target_hour, org_list, exclude_orgs=False):
    beginning_of_day = target_hour.replace(hour=0, minute=0, second=0)
    users = User.objects.filter(
        courseenrollment__schedule__start__gte=beginning_of_day,
        courseenrollment__schedule__start__lt=beginning_of_day + datetime.timedelta(days=1),
        courseenrollment__is_active=True,
    ).annotate(
        first_schedule=Min('courseenrollment__schedule__start')
    ).filter(
        first_schedule__gte=target_hour,
        first_schedule__lt=target_hour + datetime.timedelta(minutes=60)
    )

    if org_list is not None:
        if exclude_orgs:
            users = users.exclude(courseenrollment__course__org__in=org_list)
        else:
            users = users.filter(courseenrollment__course__org__in=org_list)

    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).filter(
        enrollment__user__in=users,
        start__gte=beginning_of_day,
        start__lt=beginning_of_day + datetime.timedelta(days=1),
        enrollment__is_active=True,
    ).order_by('enrollment__user__id')

    if org_list is not None:
        if exclude_orgs:
            schedules = schedules.exclude(enrollment__course__org__in=org_list)
        else:
            schedules = schedules.filter(enrollment__course__org__in=org_list)

    if "read_replica" in settings.DATABASES:
        schedules = schedules.using("read_replica")

    dashboard_relative_url = reverse('dashboard')

    for (user, user_schedules) in groupby(schedules, lambda s: s.enrollment.user):
        user_schedules = list(user_schedules)
        course_id_strs = [str(schedule.enrollment.course_id) for schedule in user_schedules]

        def absolute_url(relative_path):
            return u'{}{}'.format(settings.LMS_ROOT_URL, urlquote(relative_path))

        first_schedule = user_schedules[0]
        template_context = {
            'student_name': user.profile.name,

            'course_name': first_schedule.enrollment.course.display_name,
            'course_url': absolute_url(reverse('course_root', args=[str(first_schedule.enrollment.course_id)])),

            # This is used by the bulk email optout policy
            'course_ids': course_id_strs,

            # Platform information
            'homepage_url': encode_url(marketing_link('ROOT')),
            'dashboard_url': absolute_url(dashboard_relative_url),
            'template_revision': settings.EDX_PLATFORM_REVISION,
            'platform_name': settings.PLATFORM_NAME,
            'contact_mailing_address': settings.CONTACT_MAILING_ADDRESS,
            'social_media_urls': encode_urls_in_dict(getattr(settings, 'SOCIAL_MEDIA_FOOTER_URLS', {})),
            'mobile_store_urls': encode_urls_in_dict(getattr(settings, 'MOBILE_STORE_URLS', {})),
        }
        yield (user, first_schedule.enrollment.course.language, template_context)


def encode_url(url):
    # Sailthru has a bug where URLs that contain "+" characters in their path components are misinterpreted
    # when GA instrumentation is enabled. We need to percent-encode the path segments of all URLs that are
    # injected into our templates to work around this issue.
    parsed_url = urlparse(url)
    modified_url = parsed_url._replace(path=urlquote(parsed_url.path))
    return modified_url.geturl()


def absolute_url(relative_path):
    root = settings.LMS_ROOT_URL.rstrip('/')
    relative_path = relative_path.lstrip('/')
    return encode_url(u'{root}/{path}'.format(root=root, path=relative_path))


def encode_urls_in_dict(mapping):
    urls = {}
    for key, value in mapping.iteritems():
        urls[key] = encode_url(value)
    return urls
