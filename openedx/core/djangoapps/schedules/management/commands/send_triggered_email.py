from __future__ import print_function

import datetime

from dateutil.tz import tzutc, gettz
from django.core.management.base import BaseCommand
from django.test.utils import CaptureQueriesContext
from django.db.models import Prefetch
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import DEFAULT_DB_ALIAS, connections

from openedx.core.djangoapps.schedules.models import Schedule
from openedx.core.djangoapps.user_api.models import UserPreference

from edx_ace.message import MessageType
from edx_ace.recipient_resolver import RecipientResolver
from edx_ace import ace
from edx_ace.recipient import Recipient


from course_modes.models import CourseMode, format_course_price
from lms.djangoapps.experiments.utils import check_and_get_upgrade_link


class VerifiedUpgradeDeadlineReminder(MessageType):
    pass


class VerifiedDeadlineResolver(RecipientResolver):
    def __init__(self, target_deadline):
        self.target_deadline = target_deadline

    def send(self, msg_type):
        for (user, language, context) in build_email_context(self.target_deadline):
            msg = msg_type.personalize(
                Recipient(
                    user.username,
                    user.email,
                ),
                language,
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
            'course_verified_upgrade_url': check_and_get_upgrade_link(course, user),
            'course_verified_upgrade_price': format_course_price(course.verified_modes[0].min_price),
        }

        yield (user, course.language, template_context)
