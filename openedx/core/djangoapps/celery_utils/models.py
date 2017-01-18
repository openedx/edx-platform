"""
Models to support persistent tasks.
"""

import logging

from celery import current_app
from django.db import models
from jsonfield import JSONField
from model_utils.models import TimeStampedModel

from . import tasks

log = logging.getLogger(__name__)


class FailedTask(TimeStampedModel):
    """
    Representation of tasks that have failed
    """
    task_name = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, db_index=True)
    args = JSONField(blank=True)
    kwargs = JSONField(blank=True)
    exc = models.CharField(max_length=255)
    datetime_resolved = models.DateTimeField(blank=True, null=True, default=None, db_index=True)

    class Meta(object):
        index_together = [
            (u'task_name', u'exc'),
        ]

    def reapply(self):
        """
        Enqueue new celery task with the same arguments as the failed task.
        """
        if self.datetime_resolved is not None:
            raise TypeError(u'Cannot reapply a resolved task: {}'.format(self))
        log.info(u'Reapplying failed task: {}'.format(self))
        original_task = current_app.tasks[self.task_name]
        original_task.apply_async(
            self.args,
            self.kwargs,
            task_id=self.task_id,
            link=tasks.mark_resolved.si(self.task_id)
        )

    def __unicode__(self):
        return u'FailedTask: {task_name}, args={args}, kwargs={kwargs} ({resolution})'.format(
            task_name=self.task_name,
            args=self.args,
            kwargs=self.kwargs,
            resolution=u"not resolved" if self.datetime_resolved is None else "resolved"
        )
