"""
Celery utility code for persistent tasks.
"""

from celery import Task

from .models import FailedTask


class PersistOnFailureTask(Task):  # pylint: disable=abstract-method
    """
    Custom Celery Task base class that persists task data on failure.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        If the task fails, persist a record of the task.
        """
        if not FailedTask.objects.filter(task_id=task_id, datetime_resolved=None).exists():
            FailedTask.objects.create(
                task_name=_truncate_to_field(FailedTask, 'task_name', self.name),
                task_id=task_id,  # Fixed length UUID: No need to truncate
                args=args,
                kwargs=kwargs,
                exc=_truncate_to_field(FailedTask, 'exc', repr(exc)),
            )
        super(PersistOnFailureTask, self).on_failure(exc, task_id, args, kwargs, einfo)


def _truncate_to_field(model, field_name, value):
    """
    If data is too big for the field, it would cause a failure to
    insert, so we shorten it, truncating in the middle (because
    valuable information often shows up at the end.
    """
    field = model._meta.get_field(field_name)  # pylint: disable=protected-access
    if len(value) > field.max_length:
        midpoint = field.max_length // 2
        len_after_midpoint = field.max_length - midpoint
        first = value[:midpoint]
        sep = u'...'
        last = value[len(value) - len_after_midpoint + len(sep):]
        value = sep.join([first, last])
    return value
