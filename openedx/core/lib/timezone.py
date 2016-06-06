"""
Class and utilities for timezone settings
"""

from django.db.models.fields import CharField

from pytz import common_timezones


class TimeZoneField(CharField):
    """
    A timezone field for Django models that provides and manages timezones

    """

    TIME_ZONE_CHOICES = [(tz, tz) for tz in common_timezones]

    """
    def validate_timezone(self, timezone):

        Validates given time zone with pytz time zone library
        :param timezone: Time zone to validate
        :return: Raises error if not a valid time zone

        if not timezone in all_timezones:
            raise ValidationError('Not a valid time zone: "%s"' % timezone)
    """
