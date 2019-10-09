from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from nodebb.tasks import task_sync_badge_info_with_nodebb, task_delete_badge_info_from_nodebb
from .models import Badge


@receiver(post_save, sender=Badge)
def sync_badge_info_with_nodebb(sender, instance, update_fields, **kwargs):
    badge_info = {
        'id': instance.id,
        'name': instance.name,
        'type': instance.type,
        'threshold': instance.threshold,
        'image': instance.image
    }
    task_sync_badge_info_with_nodebb.delay(badge_info)


@receiver(post_delete, sender=Badge)
def delete_badge_info_from_nodebb(sender, instance, **kwargs):

    badge_data = {
        "id": instance.id
    }
    task_delete_badge_info_from_nodebb.delay(badge_data)
