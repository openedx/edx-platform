"""
Experimentation models
"""


from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords


class ExperimentData(TimeStampedModel):
    """
    ExperimentData stores user-specific key-values associated with experiments
    identified by experiment_id.
    .. no_pii:
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    experiment_id = models.PositiveSmallIntegerField(
        null=False, blank=False, db_index=True, verbose_name=u'Experiment ID'
    )
    key = models.CharField(null=False, blank=False, max_length=255)
    value = models.TextField()

    class Meta(object):
        index_together = (
            ('user', 'experiment_id'),
        )
        verbose_name = 'Experiment Data'
        verbose_name_plural = 'Experiment Data'
        unique_together = (
            ('user', 'experiment_id', 'key'),
        )


class ExperimentKeyValue(TimeStampedModel):
    """
    ExperimentData stores any generic key-value associated with experiments
    identified by experiment_id.
    .. no_pii:
    """
    experiment_id = models.PositiveSmallIntegerField(
        null=False, blank=False, db_index=True, verbose_name=u'Experiment ID'
    )
    key = models.CharField(null=False, blank=False, max_length=255)
    value = models.TextField()

    history = HistoricalRecords()

    class Meta(object):
        verbose_name = 'Experiment Key-Value Pair'
        verbose_name_plural = 'Experiment Key-Value Pairs'
        unique_together = (
            ('experiment_id', 'key'),
        )
