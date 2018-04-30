"""
Take the list of states from settings.RETIREMENT_STATES and forces the
RetirementState table to mirror it.

We use a foreign keyed table for this instead of just using the settings
directly to generate a `choices` tuple for the model because the states
need to be configurable by open source partners and modifying the
`choices` for a model field causes new migrations to be generated,
with a variety of unpleasant follow-on effects for the partner when
upgrading the model at a later date.
"""
from __future__ import print_function

import copy
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.user_api.models import RetirementState, UserRetirementStatus


LOGGER = logging.getLogger(__name__)

START_STATE = 'PENDING'
END_STATES = ['ERRORED', 'ABORTED', 'COMPLETE']
REQUIRED_STATES = copy.deepcopy(END_STATES)
REQUIRED_STATES.insert(0, START_STATE)
REQ_STR = ','.join(REQUIRED_STATES)


class Command(BaseCommand):
    """
    Implementation of the populate command
    """
    help = 'Populates the RetirementState table with the states present in settings.'

    def _validate_new_states(self, new_states):
        """
        Check settings for existence of states, required states
        """
        if not new_states:
            raise CommandError('settings.RETIREMENT_STATES does not exist or is empty.')

        if not set(REQUIRED_STATES).issubset(set(new_states)):
            raise CommandError('settings.RETIREMENT_STATES ({}) does not contain all required states '
                               '({})'.format(new_states, REQ_STR))

        # Confirm that the start and end states are in the right places
        if new_states.index(START_STATE) != 0:
            raise CommandError('{} must be the first state'.format(START_STATE))

        num_end_states = len(END_STATES)

        if new_states[-num_end_states:] != END_STATES:
            raise CommandError('The last {} states must be these (in this order): '
                               '{}'.format(num_end_states, END_STATES))

    def _check_current_users(self):
        """
        Check UserRetirementStatus for users currently in progress
        """
        if UserRetirementStatus.objects.exclude(current_state__state_name__in=REQUIRED_STATES).exists():
            raise CommandError(
                'Users are currently being processed. All users must be in one of these states to run this command: '
                '{}'.format(REQ_STR)
            )

    def _delete_old_states_and_create_new(self, new_states):
        """
        Wipes the RetirementState table and creates new entries based on new_states
        - Note that the state_execution_order is incremented by 10 for each entry
          this should allow manual insert of "in between" states via the Django admin
          if necessary, without having to manually re-sort all of the states.
        """

        # Save off old states before
        current_states = RetirementState.objects.all().values_list('state_name', flat=True)

        # Delete all existing rows, easier than messing with the ordering
        RetirementState.objects.all().delete()

        # Add new rows, with space in between to manually insert stages via Django admin if necessary
        curr_sort_order = 1
        for state in new_states:
            row = {
                'state_name': state,
                'state_execution_order': curr_sort_order,
                'is_dead_end_state': state in END_STATES,
                'required': state in REQUIRED_STATES
            }

            RetirementState.objects.create(**row)
            curr_sort_order += 10

        # Generate the diff
        set_current_states = set(current_states)
        set_new_states = set(new_states)

        states_to_create = set_new_states - set_current_states
        states_remaining = set_current_states.intersection(set_new_states)
        states_to_delete = set_current_states - set_new_states

        return states_to_create, states_remaining, states_to_delete

    def handle(self, *args, **options):
        """
        Execute the command.
        """
        new_states = settings.RETIREMENT_STATES
        self._validate_new_states(new_states)
        self._check_current_users()
        created, existed, deleted = self._delete_old_states_and_create_new(new_states)

        # Report
        print("All states removed and new states added. Differences:")
        print("   Added: {}".format(created))
        print("   Removed: {}".format(deleted))
        print("   Remaining: {}".format(existed))
        print("States updated successfully. Current states:")

        for state in RetirementState.objects.all():
            print(state)
