""" Tasks for sending notification to ace push channel """
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from edx_ace import ace
from edx_ace.recipient import Recipient

from .message_type import PushNotificationMessageType

User = get_user_model()
logger = get_task_logger(__name__)


def send_ace_msg_to_push_channel(audience_ids, notification_object, sender_id):
    """
    Send mobile notifications using ace to push channels.
    """
    if not audience_ids:
        return

    # We are releasing this feature gradually. For now, it is only tested with the discussion app.
    # We might have a list here in the future.
    if notification_object.app_name != 'discussion':
        return

    notification_type = notification_object.notification_type

    post_data = {
        'notification_type': notification_type,
        'course_id': str(notification_object.course_id),
        'content_url': notification_object.content_url,
        **notification_object.content_context
    }
    emails = list(User.objects.filter(id__in=audience_ids).values_list('email', flat=True))
    context = {'post_data': post_data}
    try:
        sender = User.objects.get(id=sender_id)
        # We don't need recipient since all recipients are in emails dict.
        # But PushNotificationMessageType.personalize method requires us a recipient object.
        # I have added sender here in case we might need it in future with the context.
        recipient = Recipient(sender.id, sender.email)
    except User.DoesNotExist:
        recipient = None

    message = PushNotificationMessageType(
        app_label="notifications", name="push"
    ).personalize(recipient, 'en', context)
    message.options['emails'] = emails
    message.options['braze_campaign'] = notification_type
    message.options['skip_disable_user_policy'] = True

    ace.send(message, limit_to_channels=getattr(settings, 'ACE_PUSH_CHANNELS', []))
    logger.info('Sent mobile notification for %s to ace push channel.', notification_type)
