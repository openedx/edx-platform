"""
Synchronizes the announcement list with all active students.
"""
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User

from .mailchimp_sync_course import (
    connect_mailchimp, get_cleaned,
    get_subscribed, get_unsubscribed,
    subscribe_with_data
)

log = logging.getLogger('edx.mailchimp')


class Command(BaseCommand):
    """
    Synchronizes the announcement list with all active students.
    """
    args = '<mailchimp_key mailchimp_list course_id>'
    help = 'Synchronizes the announcement list with all active students.'

    option_list = BaseCommand.option_list + (
        make_option('--key', action='store', help='mailchimp api key'),
        make_option('--list', action='store', dest='list_id',
                    help='mailchimp list id'),
    )

    def parse_options(self, options):
        """Parses `options` of the command."""
        if not options['key']:
            raise CommandError('missing key')

        if not options['list_id']:
            raise CommandError('missing list id')

        return (options['key'], options['list_id'])

    def handle(self, *args, **options):
        key, list_id = self.parse_options(options)

        log.info('Syncronizing announcement mailing list')

        mailchimp = connect_mailchimp(key)

        subscribed = get_subscribed(mailchimp, list_id)
        unsubscribed = get_unsubscribed(mailchimp, list_id)
        cleaned = get_cleaned(mailchimp, list_id)
        non_subscribed = unsubscribed.union(cleaned)

        enrolled = get_enrolled()
        exclude = subscribed.union(non_subscribed)
        to_subscribe = get_data(enrolled, exclude=exclude)

        subscribe_with_data(mailchimp, list_id, to_subscribe)


def get_enrolled():
    """
    Filter out all users who signed up via a Microsite, which UserSignupSource tracks
    """
    ## TODO (Feanil) This grabs all inactive students and MUST be changed (or, could exclude inactive users in get_data)
    return User.objects.raw('SELECT * FROM auth_user where id not in (SELECT user_id from student_usersignupsource)')


def get_data(users, exclude=None):
    """
    users: set of Django users
    exclude [optional]: set of Django users to exclude

    returns: {'EMAIL': u.email} for all users in users less those in `exclude`
    """
    exclude = exclude if exclude else set()
    emails = (u.email for u in users)
    return ({'EMAIL': e} for e in emails if e not in exclude)
