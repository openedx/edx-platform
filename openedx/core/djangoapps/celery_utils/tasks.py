"""
Celery tasks that support the utils in this module.
"""

from celery import task
from django.utils.timezone import now


@task
def mark_resolved(task_id):
    """
    Given a task_id, mark all records of that task as resolved in the
    FailedTask table
    """
    from . import models  # Imported inside the task to resolve circular imports.
    models.FailedTask.objects.filter(task_id=task_id, datetime_resolved=None).update(datetime_resolved=now())
