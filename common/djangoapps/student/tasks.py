"""
This file contains celery tasks for sending email
"""
import logging

from boto.exception import NoAuthHandlerFound
from celery.exceptions import MaxRetriesExceededError
from celery.task import task  # pylint: disable=no-name-in-module, import-error
from django.conf import settings
from django.core import mail
from mobileapps.models import MobileApp
from student.models import CourseEnrollment
from edx_notifications.lib.publisher import bulk_publish_notification_to_users


log = logging.getLogger('edx.celery.task')


@task(bind=True)
def send_activation_email(self, subject, message, from_address, dest_addr):
    """
    Sending an activation email to the user.
    """
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    retries = self.request.retries
    try:
        mail.send_mail(subject, message, from_address, [dest_addr], fail_silently=False)
        # Log that the Activation Email has been sent to user without an exception
        log.info("Activation Email has been sent to User {user_email}".format(
            user_email=dest_addr
        ))
    except NoAuthHandlerFound:  # pylint: disable=broad-except
        log.info('Retrying sending email to user {dest_addr}, attempt # {attempt} of {max_attempts}'. format(
            dest_addr=dest_addr,
            attempt=retries,
            max_attempts=max_retries
        ))
        try:
            self.retry(countdown=settings.RETRY_ACTIVATION_EMAIL_TIMEOUT, max_retries=max_retries)
        except MaxRetriesExceededError:
            log.error(
                'Unable to send activation email to user from "%s" to "%s"',
                from_address,
                dest_addr,
                exc_info=True
            )
    except Exception:  # pylint: disable=bare-except
        log.exception(
            'Unable to send activation email to user from "%s" to "%s"',
            from_address,
            dest_addr,
            exc_info=True
        )
        raise Exception


@task()
def publish_course_notifications_task(course_id, notification_msg, exclude_user_ids=None):  # pylint: disable=invalid-name
    """
    This function will call the edx_notifications api method "bulk_publish_notification_to_users"
    and run as a new Celery task.
    """
    # get the enrolled and active user_id list for this course.
    user_ids = CourseEnrollment.objects.values_list('user_id', flat=True).filter(
        is_active=1,
        course_id=course_id
    )

    try:
        bulk_publish_notification_to_users(user_ids, notification_msg, exclude_user_ids=exclude_user_ids)
        # if we have a course announcement notification publish it to urban airship too
        if notification_msg.msg_type.name == 'open-edx.studio.announcements.new-announcement':
            # fetch all active mobile apps to send notifications to all apps
            mobile_apps = MobileApp.objects.filter(is_active=True)
            for mobile_app in mobile_apps:
                channel_context = {
                    "api_credentials": mobile_app.get_api_keys()
                }
                preferred_channel = mobile_app.get_notification_provider_name()
                if preferred_channel:
                    bulk_publish_notification_to_users(
                        user_ids,
                        notification_msg,
                        exclude_user_ids=exclude_user_ids,
                        preferred_channel=preferred_channel,
                        channel_context=channel_context
                    )
    except Exception, ex:
        # Notifications are never critical, so we don't want to disrupt any
        # other logic processing. So log and continue.
        log.exception(ex)
