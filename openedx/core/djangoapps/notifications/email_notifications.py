"""
Email notifications module.
"""
from django.utils.translation import gettext_lazy as _


class EmailCadence:
    """
    Email cadence class
    """
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    IMMEDIATELY = 'Immediately'
    NEVER = 'Never'
    EMAIL_CADENCE_CHOICES = [
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (IMMEDIATELY, _('Immediately')),
        (NEVER, _('Never')),
    ]
    EMAIL_CADENCE_CHOICES_DICT = dict(EMAIL_CADENCE_CHOICES)

    @classmethod
    def get_email_cadence_choices(cls):
        """
        Returns email cadence choices.
        """
        return cls.EMAIL_CADENCE_CHOICES

    @classmethod
    def get_email_cadence_value(cls, email_cadence):
        """
        Returns email cadence display for the given email cadence.
        """
        return cls.EMAIL_CADENCE_CHOICES_DICT.get(email_cadence, None)
