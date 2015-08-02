"""
Signal handlers supporting various gradebook use cases
"""
import logging
import sys
import json
from django.dispatch import receiver
from django.conf import settings
from django.db.models.signals import post_save, pre_save

from courseware import grades
from courseware.signals import score_changed
from xmodule.modulestore import EdxJSONEncoder
from util.request import RequestMockWithoutMiddleware
from util.signals import course_deleted
from student.roles import get_aggregate_exclusion_user_ids

from gradebook.models import StudentGradebook, StudentGradebookHistory

from edx_notifications.lib.publisher import (
    publish_notification_to_user,
    get_notification_type
)
from edx_notifications.data import NotificationMessage

log = logging.getLogger(__name__)


@receiver(score_changed)
def on_score_changed(sender, **kwargs):
    """
    Listens for a 'score_changed' signal and when observed
    recalculates the specified user's gradebook entry
    """
    from courseware.views import get_course
    user = kwargs['user']
    course_key = kwargs['course_key']
    course_descriptor = get_course(course_key, depth=None)
    request = RequestMockWithoutMiddleware().get('/')
    request.user = user
    progress_summary = grades.progress_summary(user, request, course_descriptor)
    grade_summary = grades.grade(user, request, course_descriptor)
    grading_policy = course_descriptor.grading_policy
    grade = grade_summary['percent']
    proforma_grade = grades.calculate_proforma_grade(grade_summary, grading_policy)

    try:
        gradebook_entry = StudentGradebook.objects.get(user=user, course_id=course_key)
        if gradebook_entry.grade != grade:
            gradebook_entry.grade = grade
            gradebook_entry.proforma_grade = proforma_grade
            gradebook_entry.progress_summary = json.dumps(progress_summary, cls=EdxJSONEncoder)
            gradebook_entry.grade_summary = json.dumps(grade_summary, cls=EdxJSONEncoder)
            gradebook_entry.grading_policy = json.dumps(grading_policy, cls=EdxJSONEncoder)
            gradebook_entry.save()
    except StudentGradebook.DoesNotExist:
        StudentGradebook.objects.create(
            user=user,
            course_id=course_key,
            grade=grade,
            proforma_grade=proforma_grade,
            progress_summary=json.dumps(progress_summary, cls=EdxJSONEncoder),
            grade_summary=json.dumps(grade_summary, cls=EdxJSONEncoder),
            grading_policy=json.dumps(grading_policy, cls=EdxJSONEncoder)
        )


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
