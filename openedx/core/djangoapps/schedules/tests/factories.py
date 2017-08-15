import factory
import pytz

from openedx.core.djangoapps.schedules import models
from student.tests.factories import CourseEnrollmentFactory


class ScheduleFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Schedule

    start = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    upgrade_deadline = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    enrollment = factory.SubFactory(CourseEnrollmentFactory)
