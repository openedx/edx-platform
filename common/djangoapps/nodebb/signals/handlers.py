from logging import getLogger

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from common.lib.nodebb_client.client import NodeBBClient
from lms.djangoapps.onboarding.helpers import COUNTRIES
from nodebb.helpers import get_fields_to_sync_with_nodebb
from lms.djangoapps.onboarding.models import UserExtendedProfile, Organization
from nodebb.models import DiscussionCommunity
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange, UserProfile
from xmodule.modulestore.django import modulestore

log = getLogger(__name__)


def log_action_response(user, status_code, response_body):
    if status_code != 200:
        log.error("Error: Can not update user(%s) on nodebb due to %s" % (user.username, response_body))
    else:
        log.info('Success: User(%s) has been updated on nodebb' % user.username)


@receiver(post_save, sender=UserProfile)
@receiver(post_save, sender=UserExtendedProfile)
def sync_user_info_with_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """
    Sync information b/w NodeBB User Profile and Edx User Profile
    """

    fields_to_sync_with_nodebb = get_fields_to_sync_with_nodebb()
    #
    # if not kwargs.get('update_fields') or (not kwargs['update_fields'] & set(fields_to_sync_with_nodebb)) \
    #         and not created:
    #     return

    user = instance.user
    if sender == UserProfile:
        data_to_sync = {
            "city_of_residence": instance.city,
            "country_of_residence": COUNTRIES.get(instance.country.code, ''),
            "birthday": "01/01/%s" % instance.year_of_birth,
            "language": instance.language,
        }
    elif sender == UserExtendedProfile:
        data_to_sync = {
            "country_of_employment": COUNTRIES.get(instance.country_of_employment, ''),
            "city_of_employment": instance.city_of_employment,
            "interests": instance.get_user_selected_interests(),
            "focus_area": instance.get_user_selected_functions()
        }

        if instance.organization:
            data_to_sync["organization"] = instance.organization.label

    status_code, response_body = NodeBBClient().users.update_profile(user.username, kwargs=data_to_sync)
    log_action_response(user, status_code, response_body)


@receiver(post_save, sender=User, dispatch_uid='update_user_profile_on_nodebb')
def update_user_profile_on_nodebb(sender, instance, created, **kwargs):
    """
        Create user account at nodeBB when user created at edx Platform
    """
    if created:
        data_to_sync = {
            'edx_user_id': instance.id,
            'email': instance.email,
            'first_name': instance.first_name,
            'last_name': instance.last_name,
            'username': instance.username,
            'date_joined': instance.date_joined.strftime('%d/%m/%Y'),
        }

        status_code, response_body = NodeBBClient().users.create(username=instance.username, kwargs=data_to_sync)
        log_action_response(instance, status_code, response_body)

        return status_code

    else:
        data_to_sync = {
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }
        status_code, response_body = NodeBBClient().users.update_profile(instance.username, kwargs=data_to_sync)
        log_action_response(instance, status_code, response_body)


@receiver(pre_save, sender=User, dispatch_uid='activate_deactivate_user_on_nodebb')
def activate_deactivate_user_on_nodebb(sender, instance, **kwargs):
    """
    Activate or Deactivate a user on nodebb whenever user's active state changes on edx platform
    """
    current_user_obj = User.objects.filter(pk=instance.pk)

    if current_user_obj.first() and current_user_obj[0].is_active != instance.is_active:
        status_code, response_body = NodeBBClient().users.activate(username=instance.username,
                                                                   active=instance.is_active)

        log_action_response(instance, status_code, response_body)


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.create_category_on_nodebb")
def create_category_on_nodebb(sender, instance, created, **kwargs):
    """
    Create a community on NodeBB whenever a new course is created
    """
    if created:
        community_name = '%s-%s-%s-%s' % (instance.display_name, instance.id.org, instance.id.course, instance.id.run)
        status_code, response_body = NodeBBClient().categories.create(name=community_name, label=instance.display_name)

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
    """
    Automatically join a group on NodeBB [related to that course] on student enrollment
    """
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
