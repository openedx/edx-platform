from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save

from nodebb.models import TeamGroupChat
from nodebb.tasks import task_sync_badge_info_with_nodebb, task_delete_badge_info_from_nodebb
from .models import Badge, UserBadge


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


@receiver(post_delete, sender=TeamGroupChat)
def delete_user_badges(sender, instance, **kwargs):
    """
    This method will delete all user badges of a team that is to be deleted.

    It will be called when user delete its team and will be called as a post_delete
    of TeamGroupChat.
    :param sender: TeamGroupChat
    :param instance: Instance of TeamGroupChat which is deleted
    """
    UserBadge.objects.filter(community_id=instance.room_id).delete()
