"""
Signal handlers for the badging app
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from edx_notifications.data import NotificationType
from edx_notifications.lib.publisher import register_notification_type
from edx_notifications.signals import perform_type_registrations

from nodebb.models import TeamGroupChat
from nodebb.tasks import task_delete_badge_info_from_nodebb, task_sync_badge_info_with_nodebb

from .constants import EARNED_BADGE_NOTIFICATION_TYPE, JSON_NOTIFICATION_RENDERER
from .models import Badge, UserBadge


@receiver(post_save, sender=Badge)
def sync_badge_info_with_nodebb(sender, instance, update_fields, **kwargs):  # pylint: disable=unused-argument
    """When badge is created or updated in platform, sync it in NodeBB."""
    badge_info = {
        'id': instance.id,
        'name': instance.name,
        'type': instance.type,
        'threshold': instance.threshold,
        'image': instance.image
    }
    task_sync_badge_info_with_nodebb.delay(badge_info)


@receiver(post_delete, sender=Badge)
def delete_badge_info_from_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """On badge deletion, delete it from NodeBB. This will not effect any post count on NodeBB."""
    badge_data = {
        'id': instance.id
    }
    task_delete_badge_info_from_nodebb.delay(badge_data)


@receiver(post_delete, sender=TeamGroupChat)
def delete_user_badges(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    This method will delete all user badges of a team that is to be deleted.

    It will be called when user delete its team and will be called as a post_delete
    of TeamGroupChat.
    :param sender: TeamGroupChat
    :param instance: Instance of TeamGroupChat which is deleted
    """
    UserBadge.objects.filter(community_id=instance.room_id).delete()


@receiver(perform_type_registrations)
def register_notification_types(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register philu NotificationTypes.
    This will be called automatically on the Notification subsystem startup
    """
    register_notification_type(
            NotificationType(
                name=EARNED_BADGE_NOTIFICATION_TYPE,
                renderer=JSON_NOTIFICATION_RENDERER,
            )
    )
