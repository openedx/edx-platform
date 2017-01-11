"""
Celery tasks used by cms_user_tasks
"""

import logging

from celery.task import task
from celery.exceptions import MaxRetriesExceededError
from boto.exception import NoAuthHandlerFound

from django.core import mail

log = logging.getLogger('edx.celery.task')

TASK_COMPLETE_EMAIL_MAX_RETRIES = 3
TASK_COMPLETE_EMAIL_TIMEOUT = 60


@task(bind=True)
def send_task_complete_email(self, subject, message, from_address, dest_addr):
    """
    Sending an email to the users when an async task completes.
    """
    retries = self.request.retries

    try:
        mail.send_mail(subject, message, from_address, [dest_addr], fail_silently=False)
        # Log that the Activation Email has been sent to user without an exception
        log.info("Task complete email has been sent to User {user_email}".format(
            user_email=dest_addr
        ))
    except NoAuthHandlerFound:
        log.info('Retrying sending email to user {dest_addr}, attempt # {attempt} of {max_attempts}'. format(
            dest_addr=dest_addr,
            attempt=retries,
            max_attempts=TASK_COMPLETE_EMAIL_MAX_RETRIES
        ))
        try:
            self.retry(countdown=TASK_COMPLETE_EMAIL_TIMEOUT, max_retries=TASK_COMPLETE_EMAIL_MAX_RETRIES)
        except MaxRetriesExceededError:
            log.error(
                'Unable to send task completion email to user from "%s" to "%s"',
                from_address,
                dest_addr,
                exc_info=True
            )
    except Exception:  # pylint: disable=broad-except
        log.exception(
            'Unable to send task completion email to user from "%s" to "%s"',
            from_address,
            dest_addr,
            exc_info=True
        )
        raise Exception
