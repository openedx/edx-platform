from logging import getLogger

from crum import get_current_request
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver

from common.lib.nodebb_client.client import NodeBBClient
from lms.djangoapps.onboarding.helpers import COUNTRIES
from certificates.models import GeneratedCertificate
from lms.djangoapps.onboarding.models import (UserExtendedProfile, Organization, FocusArea, EmailPreference, )
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from mailchimp_pipeline.signals.handlers import send_user_info_to_mailchimp, send_user_profile_info_to_mailchimp, \
    send_user_enrollments_to_mailchimp, send_user_course_completions_to_mailchimp
from nodebb.models import DiscussionCommunity, TeamGroupChat
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED

from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange, UserProfile, CourseEnrollment
from xmodule.modulestore.django import modulestore


log = getLogger(__name__)


def log_action_response(user, status_code, response_body):
    if status_code != 200:
        log.error("Error: Can not update user(%s) on nodebb due to %s" % (user.username, response_body))
    else:
        log.info('Success: User(%s) has been updated on nodebb' % user.username)


@receiver(post_save, sender=CourseEnrollment)
def sync_enrolments_to_mailchimp(sender, instance, created, **kwargs):
    send_user_enrollments_to_mailchimp(sender, instance, created, kwargs)


@receiver(COURSE_CERT_AWARDED, sender=GeneratedCertificate)
def handle_course_cert_awarded(sender, user, course_key, **kwargs):  # pylint: disable=unused-argument
    send_user_course_completions_to_mailchimp(sender, user, course_key, kwargs)


@receiver(post_save, sender=UserProfile)
@receiver(post_save, sender=UserExtendedProfile)
@receiver(post_save, sender=EmailPreference)
@receiver(post_save, sender=Organization)
def sync_user_info_with_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """
    Sync information b/w NodeBB User Profile and Edx User Profile
    """

    request = get_current_request()
    user = request.user

    send_user_profile_info_to_mailchimp(sender, instance, kwargs)

    if 'login' in request.path or 'logout' in request.path or sender == EmailPreference:
        return

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
            "self_prioritize_areas": instance.get_user_selected_functions()
        }

        if instance.organization:
            data_to_sync["organization"] = instance.organization.label
    elif sender == Organization:
        data_to_sync = {
            "focus_area": FocusArea.objects.get(code=instance.focus_area).label if instance.focus_area else ""
        }
    else:
        pass

    status_code, response_body = NodeBBClient().users.update_profile(user.username, kwargs=data_to_sync)
    log_action_response(user, status_code, response_body)


@receiver(post_save, sender=User, dispatch_uid='update_user_profile_on_nodebb')
def update_user_profile_on_nodebb(sender, instance, created, **kwargs):
    """
        Create user account at nodeBB when user created at edx Platform
    """
    send_user_info_to_mailchimp(sender, instance, created, kwargs)

    request = get_current_request()
    if 'login' in request.path:
        return

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




@receiver(post_delete, sender=User)
def delete_user_from_nodebb(sender, **kwargs):
    """
    Delete User from NodeBB when deleted at edx (either deleted via admin-panel OR user is under age)
    """
    instance = kwargs['instance']

    status_code, response_body = NodeBBClient().users.delete_user(instance.username, kwargs={})
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


@receiver(post_save, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.create_update_groupchat_on_nodebb")
def create_update_groupchat_on_nodebb(sender, instance, created, **kwargs):
    """
    Create group on NodeBB whenever a new team is created
    OR
    Update a group whenever existing team changes
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if created or not team_group_chat:
        group_info = _get_group_data(instance)
        status_code, response_body = NodeBBClient().groups.create(**group_info)

        if status_code != 200:
            log.error(
                "Error: Can't create nodebb group for the given course %s due to %s" % (
                    instance.course_id, response_body
                )
            )
        else:
            TeamGroupChat.objects.create(team_id=instance.id, room_id=response_body['room'])
            log.info("Successfully created group for course %s" % instance.course_id)
    else:
        room_id = team_group_chat.room_id
        group_info = _get_group_data(instance, is_created=False)
        status_code, response_body = NodeBBClient().groups.update(room_id=room_id, **group_info)

        if status_code != 200:
            log.error(
                "Error: Can't update nodebb group for the given course %s due to %s" % (
                    instance.course_id, response_body
                )
            )
        else:
            log.info("Successfully updated group for course %s" % instance.course_id)


def _get_group_data(instance, is_created=True):
    group_info = {
        'team': [],
        'roomName': instance.name,
        'teamCountry': str(instance.country.name),
        'teamLanguage': instance.language,
        'teamDescription': instance.description
    }
    if is_created:
        course = CourseOverview.objects.get(id=instance.course_id)
        group_info.update({'courseName': course.display_name})

    return group_info


@receiver(pre_delete, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.delete_groupchat_on_nodebb")
def delete_groupchat_on_nodebb(sender, instance, **kwargs):
    """
    Delete group on NodeBB whenever a team is deleted
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if team_group_chat:
        status_code, response_body = NodeBBClient().groups.delete(room_id=team_group_chat.room_id)

        if status_code != 200:
            log.error(
                "Error: Can't delete nodebb group for the given course %s due to %s" % (
                    instance.course_id, response_body
                )
            )
        else:
            team_group_chat.delete()
            log.info("Successfully deleted group chat for course %s" % instance.course_id)


@receiver(post_save, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.join_groupchat_on_nodebb")
def join_groupchat_on_nodebb(sender, instance, created, **kwargs):
    """
    Join group on NodeBB whenever a new member joins a team
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.team.id).first()

    if created and team_group_chat:
        member_info = {"team": [instance.user.username, '']}
        status_code, response_body = NodeBBClient().groups.update(room_id=team_group_chat.room_id, **member_info)

        if status_code != 200:
            log.error(
                'Error: Can not join the group, user (%s, %s) due to %s' % (
                    instance.team.name, instance.user, response_body
                )
            )
        else:
            log.info('Success: User have joined the group %s successfully' % instance.team.name)


@receiver(post_delete, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.leave_groupchat_on_nodebb")
def leave_groupchat_on_nodebb(sender, instance, **kwargs):
    """
    Leave group on NodeBB whenever a member leaves a team
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.team.id).first()

    if team_group_chat:
        member_info = {"team": [instance.user.username, '']}
        status_code, response_body = NodeBBClient().groups.delete(room_id=team_group_chat.room_id, **member_info)

        if status_code != 200:
            log.error(
                'Error: Can not unjoin the group, user (%s, %s) due to %s' % (
                    instance.team.name, instance.user, response_body
                )
            )
        else:
            log.info('Success: User have unjoined the group %s successfully' % instance.team.name)
