"""
Factories for schedules tests
"""


import factory
import pytz

from openedx.core.djangoapps.schedules import models
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory


class ScheduleExperienceFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.ScheduleExperience

    experience_type = models.ScheduleExperience.EXPERIENCES.default


class ScheduleFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Schedule

    start_date = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    upgrade_deadline = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    enrollment = factory.SubFactory(CourseEnrollmentFactory)
    experience = factory.RelatedFactory(ScheduleExperienceFactory, 'schedule')


class ScheduleConfigFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.ScheduleConfig

    site = factory.SubFactory(SiteFactory)
    create_schedules = True
    enqueue_recurring_nudge = True
    deliver_recurring_nudge = True
    enqueue_upgrade_reminder = True
    deliver_upgrade_reminder = True
    enqueue_course_update = True
    deliver_course_update = True
    hold_back_ratio = 0
