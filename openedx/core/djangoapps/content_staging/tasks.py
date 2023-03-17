"""
Celery tasks for Content Staging.
"""
from datetime import timedelta
import logging
import random

from celery import shared_task
from celery_utils.logged_task import LoggedTask
from django.db import DatabaseError, NotSupportedError, transaction
from django.utils import timezone

from .models import StagedContent

log = logging.getLogger(__name__)


@shared_task(base=LoggedTask)
def delete_expired_staged_content():
    """
    A Celery task to delete StagedContent entries that are no longer relevant.
    """
    # We delete any EXPIRED, ERROR, or even LOADING entries that are older than
    # the cutoff time. We never delete content that is READY. If it's been
    # LOADING for longer than the cutoff time, we can assume an error occurred.
    current_time = timezone.now()
    expired_time = current_time - timedelta(hours=48)
    to_delete = StagedContent.objects.filter(created__lt=expired_time).exclude(status=StagedContent.Status.READY)
    to_delete_count = to_delete.count()

    if to_delete_count == 0:
        log.info("No StagedContent entries to clean up at this time.")
        return

    try:
        # Select the rows for deletion, unless some other task (maybe this same one? is deleting them). Never block,
        # just ignore rows that we can't lock.
        locked_for_delete = list(to_delete.select_for_update(skip_locked=True))
        log.info(f"Acquired lock to delete {len(locked_for_delete)} of {to_delete_count} old StagedContent entries")
        # We are locking them because in the future our StagedContent will have
        # a pre_delete signal handler to delete any associated staged static
        # asset files, and we don't want overlapping calls to do that in
        # different threads. Now that those rows are locked, we can delete them.
        for sc_row in locked_for_delete:
            # Delete this row, calling pre_delete and cascading the deletion to UserClipboard etc:
            sc_row.delete()
        log.info(f"Successfully deleted {len(locked_for_delete)} StagedContent entries")
    except NotSupportedError:
        # With MySQL < 8 we can't use skip_locked. Delete rows one at a time, so that we hopefully don't have to wait
        # too long for a lock.
        log.info(f"Deleting {to_delete_count} StagedContent entries (using individual row locking)")
        num_deleted = 0
        ids_to_delete = list(to_delete.values_list('id', flat=True))
        random.shuffle(ids_to_delete)  # Reduce chance of lock conflicts
        for pk in ids_to_delete:
            with transaction.atomic():
                try:
                    next_obj = to_delete.select_for_update().get(pk=pk)
                except StagedContent.DoesNotExist:
                    continue  # Someone else deleted it?
                except DatabaseError:
                    break  # We waited but were unable to get a lock to delete that row.
                # We have a lock on this one row; delete it, using pre_delete to delete associated data.
                next_obj.delete()
            num_deleted += 1
        if num_deleted > 0:
            log.info(f"Successfully deleted {num_deleted} StagedContent entries")
        else:
            log.error("Unable to delete any StagedContent entries")
