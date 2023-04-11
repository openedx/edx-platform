"""
Signal handlers for StagedContent
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StagedContent
from .tasks import delete_expired_clipboards

log = logging.getLogger(__name__)


@receiver(post_save, sender=StagedContent)
def trigger_celery_task(sender, instance, created, **kwargs):
    """
    Clean up old/expired StagedContent items. Instead of a scheduled task, we
    just do this every Nth time a StagedContent row is created.
    """
    if created and (instance.pk % 100) == 0:
        log.info("Enqueuing cleanup of expired StagedContent instances")
        delete_expired_clipboards.delay()
