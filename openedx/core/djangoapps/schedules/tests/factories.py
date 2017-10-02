import factory
import pytz

from openedx.core.djangoapps.schedules import models
from student.tests.factories import CourseEnrollmentFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory


class ScheduleFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Schedule

    start = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    upgrade_deadline = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    enrollment = factory.SubFactory(CourseEnrollmentFactory)


class ScheduleConfigFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.ScheduleConfig

    site = factory.SubFactory(SiteFactory)
    create_schedules = True
    enqueue_recurring_nudge = True
    deliver_recurring_nudge = True
    enqueue_upgrade_reminder = True
    deliver_upgrade_reminder = True
