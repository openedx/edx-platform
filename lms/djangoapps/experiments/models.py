from django.conf import settings
from django.db import models
from model_utils.models import TimeStampedModel


class ExperimentData(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    experiment_id = models.PositiveSmallIntegerField(
        null=False, blank=False, db_index=True, verbose_name='Experiment ID'
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
    experiment_id = models.PositiveSmallIntegerField(
        null=False, blank=False, db_index=True, verbose_name='Experiment ID'
    )
    key = models.CharField(null=False, blank=False, max_length=255)
    value = models.TextField()

    class Meta(object):
        verbose_name = 'Experiment Key-Value Pair'
        verbose_name_plural = 'Experiment Key-Value Pairs'
        unique_together = (
            ('experiment_id', 'key'),
        )
