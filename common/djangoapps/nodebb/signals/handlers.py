from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver

from common.lib.nodebb_client.client import NodeBBClient
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.create_category_on_nodebb")
def create_category_on_nodebb(sender, instance, created, **kwargs):
    if created:
        status_code, response_body = NodeBBClient().categories.create(name=instance.display_name)

        if status_code != 200:
            log.error(
                "Error: Can't create nodebb cummunity for the given course {} due to {}".format(
                    instance.id, response_body
                )
            )
        else:
            log.info('Success: Community created for course {}'.format(instance.id))


@receiver(ENROLL_STATUS_CHANGE)
def join_group_on_nodebb(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    if event == EnrollStatusChange.enroll:
        user_name = user.username
        course = modulestore().get_course(kwargs.get('course_id'))
        status_code, response_body = NodeBBClient().users.join(group_name=course.display_name,
                                                               user_name=user_name)

        if status_code != 200:
            log.error(
                'Error: Can not join the group, user ({}, {}) due to {}'.format(
                    course.display_name, user_name, response_body
                )
            )
        else:
            log.info('Success: User have joined the group {} successfully'.format(course.display_name))
