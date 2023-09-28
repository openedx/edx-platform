"""
Demographics models
"""

from django.contrib.auth import get_user_model
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords

User = get_user_model()


class UserDemographics(TimeStampedModel):
    """
    A Users Demographics platform related data in support of the Demographics
    IDA and features

    .. no_pii:
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    show_call_to_action = models.BooleanField(default=True)
    history = HistoricalRecords(app='demographics')

    class Meta:
        app_label = "demographics"
        verbose_name = "user demographic"
        verbose_name_plural = "user demographic"

    def __str__(self):
        return f'UserDemographics for {self.user}'
