import factory
import pytz

from openedx.core.djangoapps.schedules import models


class ScheduleFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = models.Schedule

    start = factory.Faker('future_datetime', tzinfo=pytz.UTC)
    upgrade_deadline = factory.Faker('future_datetime', tzinfo=pytz.UTC)
