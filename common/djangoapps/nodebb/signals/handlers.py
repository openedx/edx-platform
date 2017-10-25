from logging import getLogger

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver

from common.lib.nodebb_client.client import NodeBBClient
from lms.djangoapps.onboarding_survey.models import ExtendedProfile, UserInfoSurvey, InterestsSurvey
from nodebb.models import DiscussionCommunity
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange
from xmodule.modulestore.django import modulestore
from custom_settings.models import CustomSettings
from lms.djangoapps.onboarding_survey.signals import save_interests

log = getLogger(__name__)


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.set_is_featured_false")
def set_is_featured_false(sender, instance, created, **kwargs):
    if created:
        course_key = instance.id
        CustomSettings.objects.get_or_create(id=course_key)

        log.info("Course {} is set as not featured".format(course_key))


@receiver(post_save, sender=UserInfoSurvey)
@receiver(post_save, sender=ExtendedProfile)
@receiver(save_interests, sender=InterestsSurvey)
def sync_user_info_with_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """ Sync user information with  """
    user = instance.user

    if user:
        if sender == ExtendedProfile:
            data_to_sync = {
                "first_name": instance.first_name,
                "last_name": instance.last_name,
            }
        elif sender == UserInfoSurvey:
            data_to_sync = {
                "city_of_residence": instance.city_of_residence,
                "country_of_residence": instance.country_of_residence
            }
        elif sender == InterestsSurvey:
            data_to_sync = {
                'interests': ','.join([area.label for area in instance.capacity_areas.all()])
            }
        else:
            return

        status_code, response_body = NodeBBClient().users.update_profile(user.username, kwargs=data_to_sync)

        if status_code != 200:
            log.error(
                "Error: Can not update user(%s) on nodebb due to %s" % (user.username, response_body)
            )
        else:
            log.info('Success: User(%s) has been updated on nodebb' % user.username)


@receiver(post_save, sender=ExtendedProfile, dispatch_uid='create_user_on_nodebb')
def create_user_on_nodebb(sender, instance, created, **kwargs):
    if created:
        user_info = {
            'email': instance.user.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'username': instance.user.username,
            'organization': instance.organization.name,
            'date_joined': instance.user.date_joined,
        }

        status_code, response_body = NodeBBClient().users.create(username=instance.user.username, kwargs=user_info)

        if status_code != 200:
            log.error("Error: Can not create user(%s) on nodebb due to %s" % (instance.user.username, response_body))
        else:
            log.info('Success: User(%s) has been created on nodebb' % instance.user.username)

        return status_code


@receiver(pre_save, sender=User, dispatch_uid='activate_user_on_nodebb')
def activate_user_on_nodebb(sender, instance, **kwargs):
    if instance.is_active and User.objects.filter(pk=instance.pk, is_active=False).exists():

        status_code, response_body = NodeBBClient().users.activate(username=instance.username)

        if status_code != 200:
            log.error("Error: Can not activate user(%s) on nodebb due to %s" % (instance.username, response_body))
        else:
            log.info('Success: User(%s) has been activated on nodebb' % instance.username)


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.create_category_on_nodebb")
def create_category_on_nodebb(sender, instance, created, **kwargs):
    if created:
        community_name = '%s-%s-%s-%s' % (instance.display_name, instance.id.org, instance.id.course, instance.id.run)
        status_code, response_body = NodeBBClient().categories.create(name=community_name)

        if status_code != 200:
            log.error(
                "Error: Can't create nodebb cummunity for the given course %s due to %s" % (
                    community_name, response_body
                )
            )
        else:
            DiscussionCommunity.objects.create(
                course_id=instance.id,
                community_url=response_body.get('categoryData', {}).get('slug')
            )
            log.info('Success: Community created for course %s' % instance.id)


@receiver(ENROLL_STATUS_CHANGE)
def join_group_on_nodebb(sender, event=None, user=None, **kwargs):  # pylint: disable=unused-argument
    if event == EnrollStatusChange.enroll:
        user_name = user.username
        course = modulestore().get_course(kwargs.get('course_id'))

        community_name = '%s-%s-%s-%s' % (course.display_name, course.id.org, course.id.course, course.id.run)
        status_code, response_body = NodeBBClient().users.join(group_name=community_name, user_name=user_name)

        if status_code != 200:
            log.error(
                'Error: Can not join the group, user (%s, %s) due to %s' % (
                    course.display_name, user_name, response_body
                )
            )
        else:
            log.info('Success: User have joined the group %s successfully' % course.display_name)
