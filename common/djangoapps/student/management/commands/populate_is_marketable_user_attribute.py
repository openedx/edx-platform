""" Management command to back-populate marketing emails opt-in for the user accounts. """

import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import Exists, OuterRef

from common.djangoapps.student.models import UserAttribute
from common.djangoapps.util.query import use_read_replica_if_available

OLD_USER_ATTRIBUTE_NAME = 'marketing_emails_opt_in'
NEW_USER_ATTRIBUTE_NAME = 'is_marketable'


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms populate_is_marketable_user_attribute
    """
    help = """
        Creates a row in the UserAttribute table for all users in the platform.
        This command back-populates the 'is_marketable' attribute in the
        UserAttribute table for the user accounts.
        """

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-delay',
            type=float,
            dest='batch_delay',
            default=0.5,
            help='Time delay in each iteration'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            dest='batch_size',
            default=10000,
            help='Batch size'
        )
        parser.add_argument(
            '--start-user-id',
            type=int,
            dest='start_user_id',
            default=10000,
            help='Starting user ID'
        )
        parser.add_argument(
            '--start-userattribute-id',
            type=int,
            dest='start_userattribute_id',
            default=10000,
            help='Starting user attribute ID'
        )
        parser.add_argument(
            '--backfill-only',
            type=str,
            dest='backfill_only',
            default=None,
            help='Only backfill user attribute, renaming attribute is not required'
        )

    def _update_user_attribute(self, start_id, end_id):
        """ Updates the user attributes in batches. """
        self.stdout.write(
            f'Updating user attribute starting from ID {start_id} till {end_id}.'
        )
        return UserAttribute.objects.filter(
            id__gte=start_id,
            id__lt=end_id,
            name=OLD_USER_ATTRIBUTE_NAME
        ).order_by('id').update(name=NEW_USER_ATTRIBUTE_NAME)

    def _get_old_users_queryset(self, batch_size, marketing_opt_in_start_user_id, user_id=0):
        """
        Fetches all the old users in batches, in ascending order of id, that exist before a specified user id.
        Returns queryset of tuples with 'id' and 'is_active' field values.
        """
        self.stdout.write(f'Fetching old users in batch starting from ID {user_id} with batch size {batch_size}.')
        query_set = get_user_model().objects.filter(
            id__gt=user_id,
            id__lt=marketing_opt_in_start_user_id
        ).values_list('id', 'is_active').order_by('id')[:batch_size]
        return use_read_replica_if_available(query_set)

    def _get_recent_users_queryset(self, batch_size, user_id):
        """
        Fetches all the recent users in batches, in ascending order of id, that exist after a specified user id
        and does not have 'is_marketable' user attribute set.
        Returns queryset of tuples with 'id' and 'is_active' field values.
        """
        self.stdout.write(f'Fetching recent users in batch starting from ID {user_id} with batch size {batch_size}.')
        user_attribute_qs = UserAttribute.objects.filter(user=OuterRef('pk'), name=NEW_USER_ATTRIBUTE_NAME)
        user_query_set = get_user_model().objects.filter(
            ~Exists(user_attribute_qs),
            id__gt=user_id,
        ).values_list('id', 'is_active').order_by('id')[:batch_size]
        return use_read_replica_if_available(user_query_set)

    def _bulk_create_user_attributes(self, users):
        """ Creates the UserAttribute records in bulk. """
        last_user_id = 0
        user_attributes = []
        for user in users:
            user_attributes.append(UserAttribute(
                user_id=user[0],
                name=NEW_USER_ATTRIBUTE_NAME,
                value=str(user[1]).lower()
            ))
            last_user_id = user[0]
        try:
            UserAttribute.objects.bulk_create(user_attributes)
        except IntegrityError:
            # A UserAttribute object was already created. This could only happen if we try to create 'is_marketable'
            # user attribute that is already created. Ignore it if it does.
            self.stdout.write(f'IntegrityError raised during bulk_create having last user id: {last_user_id}.')
        return last_user_id

    def _backfill_old_users_attribute(self, batch_size, batch_delay, marketing_opt_in_start_user_id):
        """
        Backfills the is_marketable user attribute. Fetches all the old user accounts, in ascending order of id,
        that were created before a specified user id. All the fetched users do not have 'is_marketable'
        user attribute set.
        """
        users = self._get_old_users_queryset(batch_size, marketing_opt_in_start_user_id)
        while users:
            last_user_id = self._bulk_create_user_attributes(users)
            time.sleep(batch_delay)
            users = self._get_old_users_queryset(batch_size, marketing_opt_in_start_user_id, last_user_id)

    def _backfill_recent_users_attribute(self, batch_size, batch_delay, start_user_id):
        """
        Backfills the is_marketable user attribute. Fetches all the recent user accounts, in ascending order of id,
        that were created after a specified user id (start_user_id).
        This method handles the backfill of all those users that have missing user attribute even after enabling
        the MARKETING_EMAILS_OPT_IN flag.
        """
        users = self._get_recent_users_queryset(batch_size, start_user_id)
        while users:
            last_user_id = self._bulk_create_user_attributes(users)
            time.sleep(batch_delay)
            users = self._get_recent_users_queryset(batch_size, last_user_id)

    def _rename_user_attribute_name(self, batch_size, batch_delay, start_user_attribute_id):
        """ Renames the old user attribute 'marketing_emails_opt_in' to 'is_marketable'. """
        updated_records_count = 0
        start_id = start_user_attribute_id
        end_id = start_id + batch_size
        total_user_attribute_count = UserAttribute.objects.filter(name=OLD_USER_ATTRIBUTE_NAME).count()

        while updated_records_count < total_user_attribute_count:
            updated_records_count += self._update_user_attribute(start_id, end_id)
            start_id = end_id
            end_id = start_id + batch_size
            time.sleep(batch_delay)

    def handle(self, *args, **options):
        """
        This command back-populates the 'is_marketable' attribute for all existing users who do not already
        have the attribute set.
        """
        batch_delay = options['batch_delay']
        batch_size = options['batch_size']
        self.stdout.write(f'Command execution started with options: {options}.')

        if not options['backfill_only']:
            self._rename_user_attribute_name(batch_size, batch_delay, options['start_userattribute_id'])
            self._backfill_old_users_attribute(batch_size, batch_delay, options['start_user_id'])
        self._backfill_recent_users_attribute(batch_size, batch_delay, options['start_user_id'])

        self.stdout.write('Command executed successfully.')
