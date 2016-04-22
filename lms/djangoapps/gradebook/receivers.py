"""
Signal handlers supporting various gradebook use cases
"""
import logging
import sys

from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save, pre_save

from courseware.signals import score_changed
from util.signals import course_deleted
from student.roles import get_aggregate_exclusion_user_ids
from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    get_notification_type
)
from edx_notifications.data import NotificationMessage


from gradebook.models import StudentGradebook, StudentGradebookHistory
from gradebook.tasks import update_user_gradebook


log = logging.getLogger(__name__)


@receiver(score_changed, dispatch_uid="lms.courseware.score_changed")
def on_score_changed(sender, **kwargs):
    """
    Listens for a 'score_changed' signal invoke grade book update task
    """
    user = kwargs['user']
    course_key = kwargs['course_key']
    update_user_gradebook.delay(course_key, user)


@receiver(course_deleted)
def on_course_deleted(sender, **kwargs):  # pylint: disable=W0613
    """
    Listens for a 'course_deleted' signal and when observed
    removes model entries for the specified course
    """
    course_key = kwargs['course_key']
    StudentGradebook.objects.filter(course_id=course_key).delete()
    StudentGradebookHistory.objects.filter(course_id=course_key).delete()


#
# Support for Notifications, these two receivers should actually be migrated into a new Leaderboard django app.
# For now, put the business logic here, but it is pretty decoupled through event signaling
# so we should be able to move these files easily when we are able to do so
#
@receiver(pre_save, sender=StudentGradebook)
def handle_studentgradebook_pre_save_signal(sender, instance, **kwargs):
    """
    Handle the pre-save ORM event on CourseModuleCompletions
    """

    if settings.FEATURES['ENABLE_NOTIFICATIONS']:
        # attach the rank of the user before the save is completed
        data = StudentGradebook.get_user_position(
            instance.course_id,
            instance.user.id,
            exclude_users=get_aggregate_exclusion_user_ids(instance.course_id)
        )

        grade = data['user_grade']
        leaderboard_rank = data['user_position'] if grade > 0.0 else 0

        instance.presave_leaderboard_rank = leaderboard_rank


@receiver(post_save, sender=StudentGradebook)
def handle_studentgradebook_post_save_signal(sender, instance, **kwargs):
    """
    Handle the pre-save ORM event on CourseModuleCompletions
    """

    if settings.FEATURES['ENABLE_NOTIFICATIONS']:
        # attach the rank of the user before the save is completed
        data = StudentGradebook.get_user_position(
            instance.course_id,
            instance.user.id,
            exclude_users=get_aggregate_exclusion_user_ids(instance.course_id)
        )

        leaderboard_rank = data['user_position']
        grade = data['user_grade']

        # logic for Notification trigger is when a user enters into the Leaderboard
        if grade > 0.0:
            leaderboard_size = getattr(settings, 'LEADERBOARD_SIZE', 3)
            presave_leaderboard_rank = instance.presave_leaderboard_rank if instance.presave_leaderboard_rank else sys.maxint
            if leaderboard_rank <= leaderboard_size and presave_leaderboard_rank > leaderboard_size:
                try:
                    notification_msg = NotificationMessage(
                        msg_type=get_notification_type(u'open-edx.lms.leaderboard.gradebook.rank-changed'),
                        namespace=unicode(instance.course_id),
                        payload={
                            '_schema_version': '1',
                            'rank': leaderboard_rank,
                            'leaderboard_name': 'Proficiency',
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
