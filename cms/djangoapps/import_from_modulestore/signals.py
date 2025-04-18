"""
Signals for Import.
"""
from django.dispatch import receiver
from django.db.models.signals import post_save

from .data import ImportStatus
from .models import Import


@receiver(post_save, sender=Import)
def cancel_incomplete_imports(sender, instance, created, **kwargs):
    """
    Cancel any incomplete imports that have the same target as the current import.

    When a new import is created, we want to cancel any other incomplete user imports that have the same target.
    """
    if created:
        incomplete_user_imports_with_same_target = Import.objects.filter(
            user=instance.user,
            target_change=instance.target_change,
            source_key=instance.source_key,
            staged_content_for_import__isnull=False
        ).exclude(uuid=instance.uuid)
        for incomplete_import in incomplete_user_imports_with_same_target:
            incomplete_import.set_status(ImportStatus.CANCELED)
