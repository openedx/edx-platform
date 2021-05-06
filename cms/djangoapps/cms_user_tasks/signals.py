"""
Receivers of signals sent from django-user-tasks
"""
import logging
from urllib.parse import urljoin

from django.dispatch import receiver
from django.urls import reverse
from user_tasks.models import UserTaskArtifact
from user_tasks.signals import user_task_stopped

from cms.djangoapps.contentstore.toggles import bypass_olx_failure_enabled
from cms.djangoapps.contentstore.utils import course_import_olx_validation_is_enabled

from .tasks import send_task_complete_email

LOGGER = logging.getLogger(__name__)


@receiver(user_task_stopped, dispatch_uid="cms_user_task_stopped")
def user_task_stopped_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Handles sending notifications when a django-user-tasks completes.
    This is a signal receiver for user_task_stopped. Currently it only sends
    a generic "task completed" email, and only when a top-level task
    completes. Eventually it might make more sense to create specific per-task
    handlers.
    Arguments:
        sender (obj): Currently the UserTaskStatus object class
        **kwargs: See below
    Keywork Arguments:
        status (obj): UserTaskStatus of the completed task
    Returns:
        None
    """
    def get_olx_validation_from_artifact():
        """
        Get olx validation error if available for current task.
        Returns:
            olx validation string or None.
        """
        if not course_import_olx_validation_is_enabled():
            return None

        olx_artifact = UserTaskArtifact.objects.filter(status=status, name="OLX_VALIDATION_ERROR").first()
        if olx_artifact and not bypass_olx_failure_enabled():
            return olx_artifact.text

    status = kwargs['status']
    # Only send email when the entire task is complete, should only send when
    # a chain / chord / etc completes, not on sub-tasks.
    if status.parent is None:
        # `name` and `status` are not unique, first is our best guess
        artifact = UserTaskArtifact.objects.filter(status=status, name="BASE_URL").first()

        detail_url = None
        if artifact and artifact.url.startswith(('http://', 'https://')):
            detail_url = urljoin(
                artifact.url,
                reverse('usertaskstatus-detail', args=[status.uuid])
            )

        user_email = status.user.email
        task_name = status.name.lower()
        olx_validation_text = get_olx_validation_from_artifact()
        task_args = [task_name, str(status.state_text), user_email, detail_url, olx_validation_text]
        try:
            send_task_complete_email.delay(*task_args)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unable to queue send_task_complete_email")
