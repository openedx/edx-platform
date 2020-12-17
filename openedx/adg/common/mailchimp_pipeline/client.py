"""
Mailchimp client
"""
import hashlib

from django.conf import settings
from mailchimp3 import MailChimp


def _get_subscriber_hash(member_email):
    """
    Create md5 hash from email address

    Args:
        member_email (str): MD5 hash

    Returns:
        MD5 hash of email
    """
    member_email = member_email.lower().encode()
    md = hashlib.md5(member_email)
    return md.hexdigest()


class MailchimpClient(object):
    """
    Class for MailChimp client
    """

    def __init__(self):
        self._learners_list_id = settings.MAILCHIMP_LIST_ID
        self._client = MailChimp(mc_api=settings.MAILCHIMP_API_KEY)

    def create_or_update_list_member(self, email, data):
        """
        Add or update member in (audience) list

        Args:
            email (str): Email address of member
            data (dict): member data in json format

        Returns:
            None
        """
        subscriber_hash = _get_subscriber_hash(email)
        self._client.lists.members.create_or_update(
            list_id=self._learners_list_id, subscriber_hash=subscriber_hash, data=data
        )
