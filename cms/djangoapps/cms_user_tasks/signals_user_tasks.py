"""
Receivers of signals sent from django-user-tasks
"""
from django.conf import settings
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from six.moves.urllib.parse import urljoin
from user_tasks.models import UserTaskArtifact
from user_tasks.signals import user_task_stopped

from .tasks import send_task_complete_email
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


@receiver(user_task_stopped)
def task_ended_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles sending notifications when a django-user-tasks completes.

    This is a signal receiver for user_task_stopped. Currently it only sends
    a generic "task completed" email, and only when a top-level task
    completes. Eventually it might make more sense to create specific per-task
    handlers.

    Arguments:
        sender (obj): The user_tasks.models.UserTaskStatus object of the
            completed task.
        status (obj): The instance of the class for which the signal was
            sent. Ex: CourseImportTask
    Returns:
        None
    """
    status = kwargs['status']

    # Only send email when the entire task is complete, should only send when
    # a chain / chord / etc completes, not on sub-tasks.
    if status.parent is None:
        user = status.user
        dest_addr = user.email

        context = {
            'task_name': status.name,
            'task_status': status.state_text,
        }

        # `name` and `status` are not unique, first is our best guess
        artifact = UserTaskArtifact.objects.filter(status=status, name="BASE_URL").first()

        if artifact and artifact.url.startswith(('http://', 'https://')):
            context['detail_url'] = urljoin(
                artifact.url,
                reverse('usertaskstatus-detail', args=[status.uuid])
            )

        subject = render_to_string('emails/user_task_complete_email_subject.txt', context)
        # Eliminate any newlines
        subject = ''.join(subject.splitlines())
        message = render_to_string('emails/user_task_complete_email.txt', context)

        from_address = configuration_helpers.get_value(
            'email_from_address',
            settings.DEFAULT_FROM_EMAIL
        )

        send_task_complete_email.delay(subject, message, from_address, dest_addr)
