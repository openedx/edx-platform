"""
A managment command that can be used to set up Schedules with various configurations for testing.
"""

from __future__ import absolute_import

import datetime

import factory
import pytz
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand

from openedx.core.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.course_modes.tests.factories import CourseModeFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.schedules.tests.factories import ScheduleConfigFactory, ScheduleFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import XMODULE_FACTORY_LOCK, CourseFactory


class CourseDurationLimitExpirySchedule(ScheduleFactory):
    """
    A ScheduleFactory that creates a Schedule set up for Course Duration Limit expiry
    """
    start = factory.Faker('date_time_between', start_date='-21d', end_date='-21d', tzinfo=pytz.UTC)


class Command(BaseCommand):
    """
    A management command that generates schedule objects for all expected course duration limit
    email types, so that it is easy to generate test emails of all available types.
    """

    def handle(self, *args, **options):
        courses = modulestore().get_courses()

        # Find the largest auto-generated course, and pick the next sequence id to generate the next
        # course with.
        max_org_sequence_id = max([0] + [int(course.org[4:]) for course in courses if course.org.startswith('org.')])

        XMODULE_FACTORY_LOCK.enable()
        CourseFactory.reset_sequence(max_org_sequence_id + 1, force=True)
        course = CourseFactory.create(
            start=datetime.datetime.today() - datetime.timedelta(days=30),
            end=datetime.datetime.today() + datetime.timedelta(days=30),
            number=factory.Sequence('schedules_test_course_{}'.format),
            display_name=factory.Sequence(u'Schedules Test Course {}'.format),
        )
        XMODULE_FACTORY_LOCK.disable()
        course_overview = CourseOverview.load_from_module_store(course.id)
        CourseModeFactory.create(course_id=course_overview.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory.create(course_id=course_overview.id, mode_slug=CourseMode.VERIFIED)
        CourseDurationLimitExpirySchedule.create_batch(20, enrollment__course=course_overview)

        ScheduleConfigFactory.create(site=Site.objects.get(name='example.com'))
