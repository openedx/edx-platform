"""
Signal handlers supporting various progress use cases
"""
import sys
import logging

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.db.models import F
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import BlockUsageLocator
from student.roles import get_aggregate_exclusion_user_ids

from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    get_notification_type
)
from edx_notifications.data import NotificationMessage
from openedx.core.djangoapps.content.course_metadata.utils import is_progress_detached_vertical

from progress.models import StudentProgress, StudentProgressHistory, CourseModuleCompletion

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

log = logging.getLogger(__name__)


def is_valid_progress_module(content_id):
    """
    Returns boolean indicating if given module is valid for marking progress
    A valid module should be child of `vertical` and its category should be
    one of the PROGRESS_DETACHED_CATEGORIES
    """
    try:
        detached_categories = getattr(settings, 'PROGRESS_DETACHED_CATEGORIES', [])
        usage_id = BlockUsageLocator.from_string(content_id)
        module = modulestore().get_item(usage_id)
        if module and module.parent and module.parent.category == "vertical" and \
                module.category not in detached_categories and not is_progress_detached_vertical(module.parent):
            return True
        else:
            return False
    except (InvalidKeyError, ItemNotFoundError) as exception:
        log.debug("Error getting module for content_id:%s %s", content_id, exception.message)
        return False
    except Exception as exception:  # pylint: disable=broad-except
        # broad except to avoid wrong calculation of progress in case of unknown exception
        log.exception("Error getting module for content_id:%s %s", content_id, exception.message)
        return False


@receiver(post_save, sender=CourseModuleCompletion, dispatch_uid='edxapp.api_manager.post_save_cms')
def handle_cmc_post_save_signal(sender, instance, created, **kwargs):
    """
    Broadcast the progress change event
    """
    content_id = unicode(instance.content_id)
    if is_valid_progress_module(content_id):
        try:
            progress = StudentProgress.objects.get(user=instance.user, course_id=instance.course_id)
            progress.completions = F('completions') + 1
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
    # since instance.completions return F() ExpressionNode we have to pull completions from db
    progress = StudentProgress.objects.get(pk=instance.id)
    history_entry = StudentProgressHistory(
        user=instance.user,
        course_id=instance.course_id,
        completions=progress.completions
    )
    history_entry.save()


#
# Support for Notifications, these two receivers should actually be migrated into a new Leaderboard django app.
# For now, put the business logic here, but it is pretty decoupled through event signaling
# so we should be able to move these files easily when we are able to do so
#
@receiver(pre_save, sender=StudentProgress)
def handle_progress_pre_save_signal(sender, instance, **kwargs):
    """
    Handle the pre-save ORM event on CourseModuleCompletions
    """

    if settings.FEATURES['ENABLE_NOTIFICATIONS']:
        # If notifications feature is enabled, then we need to get the user's
        # rank before the save is made, so that we can compare it to
        # after the save and see if the position changes
        instance.presave_leaderboard_rank = StudentProgress.get_user_position(
            instance.course_id,
            instance.user.id,
            get_aggregate_exclusion_user_ids(instance.course_id)
        )['position']


@receiver(post_save, sender=StudentProgress)
def handle_progress_post_save_signal(sender, instance, **kwargs):
    """
    Handle the pre-save ORM event on CourseModuleCompletions
    """

    if settings.FEATURES['ENABLE_NOTIFICATIONS']:
        # If notifications feature is enabled, then we need to get the user's
        # rank before the save is made, so that we can compare it to
        # after the save and see if the position changes
        leaderboard_rank = StudentProgress.get_user_position(
            instance.course_id,
            instance.user.id,
            get_aggregate_exclusion_user_ids(instance.course_id)
        )['position']

        # logic for Notification trigger is when a user enters into the Leaderboard
        leaderboard_size = getattr(settings, 'LEADERBOARD_SIZE', 3)
        presave_leaderboard_rank = instance.presave_leaderboard_rank if instance.presave_leaderboard_rank else sys.maxint
        if leaderboard_rank <= leaderboard_size and presave_leaderboard_rank > leaderboard_size:
            try:
                notification_msg = NotificationMessage(
                    msg_type=get_notification_type(u'open-edx.lms.leaderboard.progress.rank-changed'),
                    namespace=unicode(instance.course_id),
                    payload={
                        '_schema_version': '1',
                        'rank': leaderboard_rank,
                        'leaderboard_name': 'Progress',
                    }
                )

                #
                # add in all the context parameters we'll need to
                # generate a URL back to the website that will
                # present the new course announcement
                #
                # IMPORTANT: This can be changed to msg.add_click_link() if we
                # have a particular URL that we wish to use. In the initial use case,
                # we need to make the link point to a different front end website
                # so we need to resolve these links at dispatch time
                #
                notification_msg.add_click_link_params({
                    'course_id': unicode(instance.course_id),
                })

                publish_notification_to_user(int(instance.user.id), notification_msg)
            except Exception, ex:
                # Notifications are never critical, so we don't want to disrupt any
                # other logic processing. So log and continue.
                log.exception(ex)
