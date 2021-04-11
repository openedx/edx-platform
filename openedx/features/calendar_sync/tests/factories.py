from factory.django import DjangoModelFactory
from openedx.features.calendar_sync.models import UserCalendarSyncConfig


class UserCalendarSyncConfigFactory(DjangoModelFactory):
    """
    Factory class for SiteConfiguration model
    """
    class Meta(object):
        model = UserCalendarSyncConfig

    enabled = True
