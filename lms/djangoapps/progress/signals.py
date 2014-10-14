"""
Signal handlers supporting various progress use cases
"""
import sys
import logging
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from progress.models import StudentProgress, StudentProgressHistory
from api_manager.models import CourseModuleCompletion
log = logging.getLogger(__name__)


@receiver(post_save, sender=CourseModuleCompletion, dispatch_uid='edxapp.api_manager.post_save_cms')
def handle_cmc_post_save_signal(sender, instance, created, **kwargs):
    """
    Broadcast the progress change event
    """
    content_id = unicode(instance.content_id)
    detached_categories = getattr(settings, 'PROGRESS_DETACHED_CATEGORIES', [])
    if created and not any(category in content_id for category in detached_categories):
        try:
            progress = StudentProgress.objects.get(user=instance.user, course_id=instance.course_id)
            progress.completions += 1
            progress.save()
        except ObjectDoesNotExist:
            progress = StudentProgress(user=instance.user, course_id=instance.course_id, completions=1)
            progress.save()
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logging.error("Exception type: {} with value: {}".format(exc_type, exc_value))


@receiver(post_save, sender=StudentProgress)
def save_history(sender, instance, **kwargs):  # pylint: disable=no-self-argument, unused-argument
    """
    Event hook for creating progress entry copies
    """
    history_entry = StudentProgressHistory(
        user=instance.user,
        course_id=instance.course_id,
        completions=instance.completions
    )
    history_entry.save()
