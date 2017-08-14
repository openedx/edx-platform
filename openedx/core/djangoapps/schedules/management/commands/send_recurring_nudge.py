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


class RecurringNudge(MessageType):
    def __init__(self, week):
        self.name = "RecurringNudge_Week{}".format(week)


class ScheduleStartResolver(RecipientResolver):
    def __init__(self, target_start_date):
        self.target_start_date = target_start_date

    def send(self, msg_type):
        for (user, language, context) in self.build_email_context():
            msg = msg_type.personalize(
                Recipient(
                    user.username,
                    user.email,
                ),
                language,
                context
            )
            ace.send(msg)

    def build_email_context(self):
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
            start__year=self.target_start_date.year,
            start__month=self.target_start_date.month,
            start__day=self.target_start_date.day,
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
                'student_name': user.profile.name,
                'course_name': course.display_name,
                'course_url': absolute_url(course_root),
            }

            yield (user, course.language, template_context)



class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--date', default=datetime.datetime.utcnow().date().isoformat())

    def handle(self, *args, **options):
        current_date = datetime.date(*[int(x) for x in options['date'].split('-')])

        for week in (1, 2, 3, 4):
            msg_t = RecurringNudge(week)
            target_date = current_date + datetime.timedelta(days=offset)
            ScheduleStartResolver(target_date).send(msg_t)