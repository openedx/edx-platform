from logging import getLogger

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from common.lib.nodebb_client.client import NodeBBClient
from lms.djangoapps.discussion_nodebb.models import DiscussionCommunity
from lms.djangoapps.onboarding_survey.models import ExtendedProfile
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)


@receiver(post_save, sender=ExtendedProfile, dispatch_uid='create_user_on_nodebb')
def create_user_on_nodebb(sender, instance, created, **kwargs):
    if created:
        user_info = {
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'username': instance.user.username,
            'organization': instance.organization.name,
            'date_joined': instance.user.date_joined,
        }

        status_code, response_body = NodeBBClient().users.create(username=instance.user.username, kwargs=user_info)

        if status_code != 200:
            log.error(
                "Error: Can not create user({}) on nodebb due to {}".format(instance.user.username, response_body)
            )
        else:
            log.info('Success: User({}) has been created on nodebb'.format(instance.user.username))


@receiver(pre_save, sender=User, dispatch_uid='activate_user_on_nodebb')
def activate_user_on_nodebb(sender, instance, **kwargs):
    if instance.is_active and User.objects.filter(pk=instance.pk, is_active=False).exists():

        status_code, response_body = NodeBBClient().users.activate(username=instance.username)

        if status_code != 200:
            log.error("Error: Can not activate user({}) on nodebb due to {}".format(instance.username, response_body))
        else:
            log.info('Success: User({}) has been activated on nodebb'.format(instance.username))


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.create_category_on_nodebb")
def create_category_on_nodebb(sender, instance, created, **kwargs):
    if created:
        community_name = '%s-%s-%s-%s' % (instance.display_name, instance.id.org, instance.id.course, instance.id.run)
        status_code, response_body = NodeBBClient().categories.create(name=community_name)

        if status_code != 200:
            log.error(
                "Error: Can't create nodebb cummunity for the given course {} due to {}".format(
                    community_name, response_body
                )
            )
        else:
            DiscussionCommunity.objects.create(course_id=instance.id, community_url=response_body.get('categoryData',
                                                                                                      {}).get('slug'))
            log.info('Success: Community created for course {}'.format(instance.id))


@receiver(ENROLL_STATUS_CHANGE)
def join_group_on_nodebb(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    if event == EnrollStatusChange.enroll:
        user_name = user.username
        course = modulestore().get_course(kwargs.get('course_id'))

        community_name = '%s-%s-%s-%s' % (course.display_name, course.id.org, course.id.course, course.id.run)
        status_code, response_body = NodeBBClient().users.join(group_name=community_name, user_name=user_name)

        if status_code != 200:
            log.error(
                'Error: Can not join the group, user ({}, {}) due to {}'.format(
                    course.display_name, user_name, response_body
                )
            )
        else:
            log.info('Success: User have joined the group {} successfully'.format(course.display_name))
