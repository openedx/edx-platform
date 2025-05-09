""" Tasks for sending notification to ace push channel """
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from edx_ace import ace
from edx_ace.channel import ChannelType
from edx_ace.recipient import Recipient

from .message_type import PushNotificationMessageType

User = get_user_model()
logger = get_task_logger(__name__)


def send_ace_msg_to_braze_push_channel(audience_ids, notification_object, sender_id):
    """
    Send mobile notifications using ace braze_push channel.
    """
    if not audience_ids:
        return

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
        recipient = Recipient(sender.id, sender.email)
    except User.DoesNotExist:
        recipient = None

    message = PushNotificationMessageType(
        app_label="notifications", name="braze_push"
    ).personalize(recipient, 'en', context)
    message.options['emails'] = emails
    message.options['braze_campaign'] = notification_type
    message.options['skip_disable_user_policy'] = True

    ace.send(message, limit_to_channels=[ChannelType.BRAZE_PUSH])
    logger.info('Sent mobile notification for %s to ace channel', notification_type)
