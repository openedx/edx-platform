"""
Defines the abstract interface for a class that can handle
a callback when the timer expires
"""

import logging
import pytz
import copy
from datetime import datetime, timedelta

from importlib import import_module

from django.dispatch import receiver
from edx_notifications.data import NotificationCallbackTimer
from edx_notifications.exceptions import ItemNotFoundError

from edx_notifications.stores.store import notification_store
from edx_notifications import const

from edx_notifications.signals import perform_notification_scan, perform_timer_registrations

PURGE_NOTIFICATIONS_TIMER_NAME = 'purge-notifications-timer'

log = logging.getLogger(__name__)


@receiver(perform_notification_scan)  # tie into the background_check management command execution
def poll_and_execute_timers(**kwargs):  # pylint: disable=unused-argument
    """
    Will look in our registry of timers and see which should be executed now. It is not
    advised to call this method on any webservers that are serving HTTP traffic as
    this can take an arbitrary amount of time
    """

    log.info('Starting poll_and_execute_timers()...')
    store = notification_store()

    timers_not_executed = store.get_all_active_timers()

    for timer in timers_not_executed:
        log.info('Executing timer: {timer}...'.format(timer=str(timer)))

        timer.executed_at = datetime.now(pytz.UTC)
        store.save_notification_timer(timer)

        try:
            module_path, _, name = timer.class_name.rpartition('.')
            log.info('Creating TimerCallback at class_name "{class_name}"'.format(class_name=timer.class_name))

            class_ = getattr(import_module(module_path), name)
            handler = class_()

            results = handler.notification_timer_callback(timer)

            # store a copy of the results in the database record
            # for the timer
            timer.results = copy.deepcopy(results)

            # successful, see if we should reschedule
            rerun_delta = results.get('reschedule_in_mins')
            rerun_delta = rerun_delta if rerun_delta else timer.periodicity_min

            if rerun_delta:
                min_delta = const.NOTIFICATION_MINIMUM_PERIODICITY_MINS
                rerun_delta = rerun_delta if rerun_delta >= min_delta else min_delta

                timer.callback_at = timer.callback_at + timedelta(minutes=rerun_delta)

                # is the rescheduling still in the past?
                if timer.callback_at < datetime.now(pytz.UTC):
                    timer.callback_at = datetime.now(pytz.UTC) + timedelta(minutes=rerun_delta)

                timer.executed_at = None  # need to reset this or it won't get picked up again

            if results.get('errors'):
                timer.err_msg = str(results['errors'])

            # see if the callback returned a 'context_update'
            # which means that we should persist this in
            # the timer context
            if 'context_update' in results:
                timer.context.update(results['context_update'])

            store.save_notification_timer(timer)
        except Exception, ex:  # pylint: disable=broad-except
            # generic error (possibly couldn't create class_name instance?)
            timer.err_msg = str(ex)
            timer.is_active = False
            store.save_notification_timer(timer)

            log.exception(ex)

    log.info('Ending poll_and_execute_timers()...')


@receiver(perform_timer_registrations)
def register_purge_notifications_timer(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register PurgeNotificationsCallbackHandler.
    This will be called automatically on the Notification subsystem startup (because we are
    receiving the 'perform_timer_registrations' signal)
    """
    store = notification_store()

    try:
        store.get_notification_timer(PURGE_NOTIFICATIONS_TIMER_NAME)
    except ItemNotFoundError:
        # Set first execution time at upcoming 1:00 AM (1 hour after midnight).
        first_execution_at = (datetime.now(pytz.UTC) + timedelta(days=1)).replace(hour=1, minute=0, second=0)

        purge_notifications_timer = NotificationCallbackTimer(
            name=PURGE_NOTIFICATIONS_TIMER_NAME,
            callback_at=first_execution_at,
            class_name='edx_notifications.callbacks.PurgeNotificationsCallbackHandler',
            is_active=True,
            periodicity_min=const.MINUTES_IN_A_DAY
        )
        store.save_notification_timer(purge_notifications_timer)
