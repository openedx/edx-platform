import datetime
import pytz

from django.core.management.base import BaseCommand
from student.models import CourseEnrollment
from django.contrib.sites.models import Site
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig


class Command(BaseCommand):

    def handle(self, *args, **options):
        self._create_schedule_config_if_none_exists()
        self._create_schedule_if_none_exist()
        self._update_schedules()

    def _create_schedule_config_if_none_exists(self):
        schedule_configs = self._get_all_schedule_configs()
        if len(schedule_configs) == 0:
            self._create_schedule_config()
            print "Creating ScheduleConfig."

    def _create_schedule_if_none_exist(self):
        schedules = self._get_all_schedules()
        if len(schedules) == 0:
            a_schedule = self._create_schedule()
            print "Creating schedule.\nstart: {}\nupgrade_deadline: {}".format(a_schedule.start,
                                                                               a_schedule.upgrade_deadline)

    def _update_schedules(self):
        schedules = self._get_all_schedules()
        assert(len(schedules) > 0)

        for a_schedule in schedules:
            # TODO: Rewrite _calculate_n_days_from_now to be _calculate_n_days_from_date_m. Rewrite all offset calcs in
            #       terms of new function
            three_days_after_start = a_schedule.start + datetime.timedelta(days=3)
            twenty_one_days_before_upgrade_deadline = a_schedule.upgrade_deadline - datetime.timedelta(days=21)

            if three_days_after_start.day < self._now().day:
                new_start = self._calculate_n_days_from_now(n=-3)
                print "Updating 'start' from {0} to {1}".format(a_schedule.start, new_start)
                a_schedule.start = new_start

            if twenty_one_days_before_upgrade_deadline.day != self._now().day:
                new_upgrade_deadline = self._calculate_n_days_from_now(n=21)
                print "Updating 'upgrade_deadline' from {0} to {1}".format(a_schedule.upgrade_deadline,
                                                                           new_upgrade_deadline)
                a_schedule.upgrade_deadline = new_upgrade_deadline

            a_schedule.save()

    def _get_all_schedule_configs(self):
        return ScheduleConfig.objects.all()

    def _get_all_schedules(self):
        return Schedule.objects.all()

    def _create_schedule(self):
        honor_enrollment = CourseEnrollment.objects.get(id=1)
        honor_enrollment.course.self_paced = True
        a_schedule = Schedule.objects.create(start=self._calculate_n_days_from_now(n=-3),
                                             upgrade_deadline=self._calculate_n_days_from_now(n=21),
                                             enrollment=honor_enrollment)
        a_schedule.save()
        return a_schedule

    def _create_schedule_config(self):
        example_dot_com = Site.objects.get(name="example.com")
        ScheduleConfig.objects.create(site=example_dot_com,
                                      enabled=True,
                                      create_schedules=True,
                                      enqueue_recurring_nudge=True,
                                      deliver_recurring_nudge=True,
                                      enqueue_upgrade_reminder=True,
                                      deliver_upgrade_reminder=True)

    def _calculate_n_days_from_now(self, n):
        return self._now() + datetime.timedelta(days=n)

    def _now(self):
        return datetime.datetime.now(tz=pytz.UTC)
