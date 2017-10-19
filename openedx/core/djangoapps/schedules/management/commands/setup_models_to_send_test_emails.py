import datetime
import pytz
import factory

from django.core.management.base import BaseCommand
from student.models import CourseEnrollment
from django.contrib.sites.models import Site
from openedx.core.djangoapps.schedules.models import Schedule, ScheduleConfig, ScheduleExperience
from openedx.core.djangoapps.schedules.tests.factories import ScheduleFactory, ScheduleConfigFactory, ScheduleExperienceFactory
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.factories import CourseFactory, XMODULE_FACTORY_LOCK
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore


class ThreeDayNudgeSchedule(ScheduleFactory):
    start = factory.Faker('date_time_between', start_date='-3d', end_date='-3d', tzinfo=pytz.UTC)


class TenDayNudgeSchedule(ScheduleFactory):
    start = factory.Faker('date_time_between', start_date='-10d', end_date='-10d', tzinfo=pytz.UTC)


class UpgradeReminderSchedule(ScheduleFactory):
    start = factory.Faker('past_datetime', tzinfo=pytz.UTC)
    upgrade_deadline = factory.Faker('date_time_between', start_date='+2d', end_date='+2d', tzinfo=pytz.UTC)


class ContentHighlightSchedule(ScheduleFactory):
    start = factory.Faker('date_time_between', start_date='-7d', end_date='-7d', tzinfo=pytz.UTC)
    experience = factory.RelatedFactory(ScheduleExperienceFactory, 'schedule', experience_type=ScheduleExperience.EXPERIENCES.course_updates)


class Command(BaseCommand):
    """
    A management command that generates schedule objects for all expected schedule email types, so that it is easy to
    generate test emails of all available types.
    """

    def handle(self, *args, **options):
        courses = modulestore().get_courses()

        # Find the largest auto-generated course, and pick the next sequence id to generate the next
        # course with.
        max_org_sequence_id = max(int(course.org[4:]) for course in courses if course.org.startswith('org.'))

        XMODULE_FACTORY_LOCK.enable()
        CourseFactory.reset_sequence(max_org_sequence_id + 1, force=True)
        course = CourseFactory(
            start=datetime.datetime.today() - datetime.timedelta(days=30),
            end=datetime.datetime.today() + datetime.timedelta(days=30),
            number=factory.Sequence('schedules_test_course_{}'.format),
            display_name=factory.Sequence('Schedules Test Course {}'.format),
        )
        XMODULE_FACTORY_LOCK.disable()
        course_overview = CourseOverview.load_from_module_store(course.id)
        ThreeDayNudgeSchedule.create(enrollment__course=course_overview)
        TenDayNudgeSchedule.create(enrollment__course=course_overview)
        UpgradeReminderSchedule.create(enrollment__course=course_overview)
        ContentHighlightSchedule.create(enrollment__course=course_overview)

        ScheduleConfigFactory.create(site=Site.objects.get(name='example.com'))
