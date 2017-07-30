from __future__ import print_function

import datetime
import textwrap

from dateutil.tz import tzutc, gettz
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from django.utils.translation import override as override_language
from jinja2 import Environment, contextfilter, Markup, escape
from django.test.utils import CaptureQueriesContext
from django.db.models import Prefetch

from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.schedules.tasks import send_email_batch
from openedx.core.djangoapps.user_api.models import UserPreference

from django.db import DEFAULT_DB_ALIAS, connections
from django.template.loader import get_template

from edx_ace.message import MessageType
from edx_ace.recipient_resolver import RecipientResolver
from edx_ace import ace
from edx_ace.recipient import Recipient

from collections import namedtuple

from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from course_modes.models import CourseMode, format_course_price
from lms.djangoapps.commerce.utils import EcommerceService
from util.date_utils import strftime_localized


class VerifiedUpgradeDeadlineReminder(MessageType):
    pass


class VerifiedDeadlineResolver(RecipientResolver):
    def __init__(self, target_deadline):
        self.target_deadline = target_deadline

    def send(self, msg_type):
        for (user, context) in build_email_context(self.target_deadline):
            msg = msg_type.personalize(
                Recipient(
                    user.username,
                    user.email,
                ),
                context
            )
            ace.send(msg)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--date', default=datetime.datetime.utcnow().date().isoformat())

    def handle(self, *args, **options):
        current_date = datetime.date(*[int(x) for x in options['date'].split('-')])

        msg_t = VerifiedUpgradeDeadlineReminder()

        for offset in (2, 9, 16):
            target_date = current_date + datetime.timedelta(days=offset)
            VerifiedDeadlineResolver(target_date).send(msg_t)



def get_upgrade_link(enrollment):
    user = enrollment.user
    course_id = enrollment.course_id

    if not enrollment.is_active:
        return None

    if enrollment.mode not in CourseMode.UPSELL_TO_VERIFIED_MODES:
        return None

    ecommerce_service = EcommerceService()
    if ecommerce_service.is_enabled(user):
        course_mode = enrollment.course.verified_modes[0]
        return ecommerce_service.get_checkout_page_url(course_mode.sku)
    return reverse('verify_student_upgrade_and_verify', args=(course_id,))


from django.db import connection


def build_email_context(schedule_deadline):
    schedules = Schedule.objects.select_related(
        'enrollment__user__profile',
        'enrollment__course',
    ).prefetch_related(
        Prefetch(
            'enrollment__course__modes',
            queryset=CourseMode.objects.filter(mode_slug=CourseMode.VERIFIED),
            to_attr='verified_modes'
        ),
        Prefetch(
            'enrollment__user__preferences',
            queryset=UserPreference.objects.filter(key='time_zone'),
            to_attr='tzprefs'
        ),
    ).filter(
        upgrade_deadline__year=schedule_deadline.year,
        upgrade_deadline__month=schedule_deadline.month,
        upgrade_deadline__day=schedule_deadline.day,
    )

    conn = connections[DEFAULT_DB_ALIAS]
    capture = CaptureQueriesContext(conn)
    with capture:
        for schedule in schedules:
            enrollment = schedule.enrollment
            user = enrollment.user

            user_time_zone = tzutc()
            for preference in user.tzprefs:
                user_time_zone = gettz(preference.value)

            course_id_str = str(enrollment.course_id)
            course = enrollment.course

            course_root = reverse('course_root', kwargs={'course_id': course_id_str})

            def absolute_url(relative_path):
                return u'{}{}'.format(settings.LMS_ROOT_URL, relative_path)

            template_context = {
                'user_full_name': user.profile.name,
                'user_personal_address': user.profile.name if user.profile.name else user.username,
                'user_username': user.username,
                'user_time_zone': user_time_zone,
                'user_schedule_start_time': schedule.start,
                'user_schedule_verified_upgrade_deadline_time': schedule.upgrade_deadline,
                'course_id': course_id_str,
                'course_title': course.display_name,
                'course_url': absolute_url(course_root),
                'course_image_url': absolute_url(course.course_image_url),
                'course_end_time': course.end,
                'course_verified_upgrade_url': get_upgrade_link(enrollment),
                'course_verified_upgrade_price': format_course_price(course.verified_modes[0].min_price),
                'course_language': course.language,
            }

            yield (user, template_context)

    if len(capture.captured_queries) > 4:
        for query in capture.captured_queries:
            print(query['sql'])
        raise Exception()