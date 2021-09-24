"""
Django admin command to send message email emails.
"""
from datetime import datetime
from logging import getLogger
from django.core.management.base import BaseCommand

from openedx.features.wikimedia_features.messenger.models import Inbox, Message
from openedx.features.wikimedia_features.messenger.task import send_unread_messages_email_task

log = getLogger(__name__)


class Command(BaseCommand):
    """
    This command will check and send emails for pending msgs to the related users.
        $ ./manage.py lms check_and_send_pending_message_email
    """
    help = 'Command to check and send messenger emails for unread messages notification'

    def _get_notification_data(self):
        """
        it will traverse Inbox objects and return data (dict) that can be used to send notification of
        unread msgs to the users.

        Example:
        if username1 has 2 unread msgs from two channels (username2, username3) and
        username4 has 7 unread msgs from single channel (username5)
        then return dict will contain following data.

        {
            "username1":
            {
                "unread_count": 2,
                "from_users": [username2, username3]
            }
            "username4":
            {
                "unread_count": 7,
                "from_users": [username5]
            }
        }
        """
        data = {}
        inboxes = Inbox.objects.filter(unread_count__gte=1).prefetch_related('last_message')
        for inbox in inboxes:
            if inbox.last_message.receiver.username in data:
                user_dict = data[inbox.last_message.receiver.username]
                user_dict["unread_count"] += inbox.unread_count
                from_list = user_dict.get("from_users")
                from_list.append(inbox.last_message.sender.username)
                user_dict["from_users"] = from_list
                data[inbox.last_message.receiver.username] = user_dict
            else:
                data[inbox.last_message.receiver.username] = {
                    "unread_count": inbox.unread_count,
                    "from_users": [inbox.last_message.sender.username]
                }
        return data

    def _log_final_report(self, data):
        log.info('\n\n\n')
        log.info("--------------------- PENDING MESSAGES EMAILS STATS - {} ---------------------".format(
            datetime.now().date().strftime("%m-%d-%Y")
        ))
        log.info('Total number of users with pending msgs: {}'.format(len(data.keys())))
        log.info('Data gathered to send email: {}'.format(data))

    def handle(self, *args, **options):
        data = self._get_notification_data()
        self._log_final_report(data)
        send_unread_messages_email_task.delay(data)
