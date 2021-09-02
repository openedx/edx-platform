from django.db.models.signals import post_save
from django.db.models import Q
from django.dispatch import receiver


from openedx.features.wikimedia_features.messenger.models import Inbox, Message


@receiver(post_save, sender=Message)
def create_default_group(sender, instance, created, **kwargs):
    """
    On new message update last_message in inbox
    """
    if not created:
        return

    try:
        inbox = Inbox.objects.get(
            Q(last_message__sender=instance.sender, last_message__receiver=instance.receiver) |
            Q(last_message__sender=instance.receiver, last_message__receiver=instance.sender)
        )
        if inbox.last_message.sender == instance.sender:
            inbox.unread_count += 1
        else:
            inbox.unread_count = 1
        inbox.last_message = instance
        inbox.save()
    except Inbox.DoesNotExist:
        Inbox.objects.create(
            last_message=instance,
            unread_count=1
        )
