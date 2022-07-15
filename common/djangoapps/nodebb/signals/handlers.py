"""
Handlers for Nodebb app
"""
from logging import getLogger

from crum import get_current_request
from django.contrib.auth.models import User
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from common.lib.nodebb_client.client import NodeBBClient
from common.lib.hubspot_client.handlers import send_user_info_to_hubspot, send_user_enrollments_to_hubspot
from lms.djangoapps.onboarding.helpers import COUNTRIES
from lms.djangoapps.onboarding.models import FocusArea, Organization, UserExtendedProfile
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from nodebb.helpers import get_community_id
from nodebb.models import DiscussionCommunity, TeamGroupChat
from nodebb.tasks import (
    task_activate_user_on_nodebb,
    task_create_user_on_nodebb,
    task_delete_user_on_nodebb,
    task_join_group_on_nodebb,
    task_un_join_group_on_nodebb,
    task_update_user_profile_on_nodebb
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.badging.models import UserBadge
from student.models import CourseEnrollment, UserProfile
from util.model_utils import get_changed_fields_dict

log = getLogger(__name__)


def log_action_response(user, status_code, response_body):
    if status_code != 200:
        log.error("Error: Can not update user(%s) on nodebb due to %s", user.username, response_body)
    else:
        log.info('Success: User(%s) has been updated on nodebb', user.username)


@receiver(pre_save, sender=UserProfile)
def user_profile_pre_save_callback(sender, **kwargs):
    """
    Capture old fields on the user_profile instance before save and cache them as a
    private field on the current model for use in the post_save callback.
    """
    user_profile = kwargs['instance']
    user_profile._updated_fields = get_changed_fields_dict(user_profile, sender)  # pylint: disable=protected-access


@receiver(post_save, sender=UserProfile)
def sync_user_profile_info_with_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Updates city, country, year_of_birth and language fields if any of them are updated for a user
    """
    updated_fields = getattr(instance, '_updated_fields', {})

    relevant_signal_fields = ['city', 'country', 'year_of_birth', 'language']

    if not any([field in updated_fields for field in relevant_signal_fields]):
        return

    user = instance.user
    data_to_sync = {
        "city_of_residence": instance.city,
        "country_of_residence": COUNTRIES.get(instance.country.code, ''),
        "birthday": "01/01/%s" % instance.year_of_birth,
        "language": instance.language,
    }
    task_update_user_profile_on_nodebb.delay(
        username=user.username, profile_data=data_to_sync)


@receiver(post_save, sender=UserExtendedProfile)
def sync_extended_profile_info_with_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Updates country_of_employment, city_of_employment, interests, function_areas and organization fields if any of the
    first four fields mentioned are updated for a user
    """
    request = get_current_request()

    user = instance.user

    changed_fields = getattr(instance, '_changed_fields', {})

    relevant_signal_fields = ('country_of_employment', 'city_of_employment', 'interests', 'function_areas')

    # return if fields to be updated on nodebb haven't changed
    if not request or not any([field in changed_fields for field in relevant_signal_fields]):
        return

    data_to_sync = {
        "country_of_employment": COUNTRIES.get(instance.country_of_employment, ''),
        "city_of_employment": instance.city_of_employment,
        "interests": instance.get_user_selected_interests(),
        "self_prioritize_areas": instance.get_user_selected_functions()
    }

    if instance.organization:
        data_to_sync["organization"] = instance.organization.label

    # sanity to confirm that some data actually exists to sync, during registration
    if 'registration' not in request.path or any(data_to_sync.values()):
        task_update_user_profile_on_nodebb.delay(
            username=user.username, profile_data=data_to_sync)


@receiver(post_save, sender=Organization)
def sync_organization_info_with_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Sync information b/w NodeBB User Profile and Edx User Profile
    """

    # To prevent unnecessary API calls in case Django only updates
    # updated_at etc.
    request = get_current_request()
    focus_area = FocusArea.objects.get(code=instance.focus_area).label if instance.focus_area else ''

    # For anonymous user username is empty('') so we can't sync with nodebb
    if request is None or not focus_area or request.user.is_anonymous():
        return

    data_to_sync = {
        "focus_area": focus_area
    }

    user = request.user

    task_update_user_profile_on_nodebb.delay(
        username=user.username, profile_data=data_to_sync)


@receiver(post_save, sender=User, dispatch_uid='update_user_profile_on_nodebb')
def update_user_profile_on_nodebb(sender, instance, created, **kwargs):
    """
        Create user account at nodeBB when user created at edx Platform
    """
    send_user_info_to_hubspot(sender, instance, created, kwargs)

    request = get_current_request()
    if not request or 'login' in request.path:
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

        task_create_user_on_nodebb.delay(
            username=instance.username, user_data=data_to_sync)
    else:
        # sync only if fields are updated
        changed_fields = getattr(instance, '_changed_fields', {})
        relevant_signal_fields = ['first_name', 'last_name']

        if not any([field in changed_fields for field in relevant_signal_fields]):
            return

        data_to_sync = {
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }

        task_update_user_profile_on_nodebb.delay(
            username=instance.username, profile_data=data_to_sync)


@receiver(post_delete, sender=User)
def delete_user_from_nodebb(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Delete User from NodeBB when deleted at edx (either deleted via admin-panel OR user is under age)
    """
    instance = kwargs['instance']

    task_delete_user_on_nodebb.delay(username=instance.username)


@receiver(pre_save, sender=User, dispatch_uid='activate_deactivate_user_on_nodebb')
def activate_deactivate_user_on_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Activate or Deactivate a user on nodebb whenever user's active state changes on edx platform
    """
    current_user_obj = User.objects.filter(pk=instance.pk)

    if current_user_obj.first() and current_user_obj[0].is_active != instance.is_active:
        task_activate_user_on_nodebb.delay(
            username=instance.username, active=instance.is_active)


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.create_category_on_nodebb")
def create_category_on_nodebb(instance, **kwargs):  # pylint: disable=unused-argument
    """
    Create a community on NodeBB if it's already not exists
    """
    community_exists = DiscussionCommunity.objects.filter(course_id=instance.id).first()

    """
    Following code is to block the double community creation.
    When ever a course created CourseOverviews's post_save triggered twice
    On the base of function call trace we allow one of those whose 5th function
    in trace is '_listen_for_course_publish'
    """  # pylint: disable=pointless-string-statement
    import inspect
    curframe = inspect.currentframe()
    main_triggerer_function = inspect.getouterframes(curframe)[5][3]

    if not community_exists and main_triggerer_function == '_listen_for_course_publish':
        community_name = '%s-%s-%s-%s' % (instance.display_name,
                                          instance.id.org, instance.id.course, instance.id.run)
        status_code, response_body = NodeBBClient().categories.create(
            name=community_name, label=instance.display_name)

        if status_code != 200:
            log.error(
                "Error: Can't create nodebb cummunity for the given course %s due to %s",
                community_name,
                response_body
            )
        else:
            DiscussionCommunity.objects.create(
                course_id=instance.id,
                community_url=response_body.get('categoryData', {}).get('slug')
            )
            log.info('Success: Community created for course %s', instance.id)


@receiver(post_save, sender=CourseEnrollment)
def manage_membership_on_nodebb_group(instance, **kwargs):
    """
    Automatically join or unjoin a group on NodeBB [related to that course] on student enrollment
    Why we can't listen ENROLL_STATUS_CHANGE here?
    Because that triggered before completion 'create_category_on_nodebb' so this fails to
    join the course author in the category
    """

    course_id = instance.course_id
    username = instance.user.username
    community_id = get_community_id(course_id)

    if instance.is_active is True:
        task_join_group_on_nodebb.delay(
            category_id=community_id, username=username)
    elif instance.is_active is False and not kwargs['created']:
        task_un_join_group_on_nodebb.delay(
            category_id=community_id, username=username)
        # We have to sync user enrollments only in case of
        # un-enroll because
        send_user_enrollments_to_hubspot(instance.user)


@receiver(pre_delete, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.delete_groupchat_on_nodebb")
def delete_groupchat_on_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Delete group on NodeBB whenever a team is deleted
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if team_group_chat and not team_group_chat.slug:
        status_code, response_body = NodeBBClient().groups.delete(
            room_id=team_group_chat.room_id)

        if status_code != 200:
            log.error(
                "Error: Can't delete nodebb group for the given course %s due to %s", instance.course_id, response_body
            )
        else:
            team_group_chat.delete()
            log.info("Successfully deleted group chat for course %s", instance.course_id)


# TODO: following method is obsolete
@receiver(post_save, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.join_groupchat_on_nodebb")
def join_groupchat_on_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Join group on NodeBB whenever a new member joins a team
    """
    team_group_chat = TeamGroupChat.objects.filter(
        team_id=instance.team.id).first()

    if created and team_group_chat and not team_group_chat.slug:
        member_info = {"team": [instance.user.username, '']}
        status_code, response_body = NodeBBClient().groups.update(
            room_id=team_group_chat.room_id, **member_info)

        if status_code != 200:
            log.error(
                'Error: Can not join the group, user (%s, %s) due to %s',
                instance.team.name,
                instance.user,
                response_body
            )
        else:
            log.info('Success: User have joined the group %s successfully', instance.team.name)


# TODO: following method is obsolete
@receiver(post_delete, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.leave_groupchat_on_nodebb")
def leave_groupchat_on_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Leave group on NodeBB whenever a member leaves a team
    """
    team_group_chat = TeamGroupChat.objects.filter(
        team_id=instance.team.id).first()

    if team_group_chat and not team_group_chat.slug:
        member_info = {"team": [instance.user.username, '']}
        status_code, response_body = NodeBBClient().groups.delete(
            room_id=team_group_chat.room_id, **member_info)

        if status_code != 200:
            log.error(
                'Error: Can not unjoin the group, user (%s, %s) due to %s',
                instance.team.name,
                instance.user,
                response_body
            )
        else:
            log.info('Success: User have unjoined the group %s successfully', instance.team.name)


@receiver(post_save, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.create_update_team_subcategory_on_nodebb")
def create_update_team_subcategory_on_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Create subcategory on NodeBB whenever a new team is created
    OR
    Update a subcategory whenever existing team changes
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if created or not team_group_chat:
        subcategory_info = _get_team_subcategory_data(instance)
        status_code, response_body = NodeBBClient().categories.create(**subcategory_info)

        if status_code != 200:
            log.error(
                "Error: Can't create nodebb subcategory for the given course team %s due to %s",
                instance.name,
                response_body
            )
        else:
            TeamGroupChat.objects.create(
                team_id=instance.id, slug=response_body['categoryData']['slug'],
                room_id=response_body['categoryData']['cid']
            )
            log.info("Successfully created subcategory for course team %s", instance.name)
    else:
        # TODO: NodeBB client doesn't have update category method
        pass


def _get_team_subcategory_data(instance):
    """
    Returns information of a subcategory for the given course team

    Arguments:
        instance: CourseTeam object

    Returns:
        dict
    """
    subcategory_info = {
        'name': '{}-{}'.format(instance.name, instance.id),
        'label': instance.name,
        'parent_cid': int(get_community_id(instance.course_id))
    }

    return subcategory_info


@receiver(
    post_save, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.join_team_subcategory_on_nodebb"
)
def join_team_subcategory_on_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Join team subcategory on NodeBB whenever a new member joins a team
    """
    team_group_chat = TeamGroupChat.objects.filter(
        team_id=instance.team.id).first()

    if created and team_group_chat and team_group_chat.slug:
        status_code, response_body = NodeBBClient().users.join(
            username=instance.user.username, category_id=team_group_chat.room_id
        )

        if status_code != 200:
            log.error(
                'Error: Can not join team subcategory, user (%s, %s) due to %s',
                instance.team.name,
                instance.user.username,
                response_body
            )
        else:
            UserBadge.assign_missing_team_badges(instance.user.id, instance.team.id)
            log.info('Success: User has joined team subcategory %s successfully', instance.team.name)


@receiver(
    post_delete, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.leave_team_subcategory_on_nodebb"
)
def leave_team_subcategory_on_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Leave team subcategory on NodeBB whenever a member leaves a shootingteam
    """
    team_group_chat = TeamGroupChat.objects.filter(
        team_id=instance.team.id).first()

    if team_group_chat and team_group_chat.slug:
        status_code, response_body = NodeBBClient().users.un_join(
            username=instance.user.username, category_id=team_group_chat.room_id
        )

        if status_code != 200:
            log.error(
                'Error: Can not leave team subcategory, user (%s, %s) due to %s',
                instance.team.name,
                instance.user.username,
                response_body
            )
        else:
            log.info('Success: User has left team subcategory %s successfully', instance.team.name)


@receiver(pre_delete, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.delete_team_subcategory_on_nodebb")
def delete_team_subcategory_on_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Delete team subcategory on NodeBB whenever a team is deleted
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if team_group_chat and team_group_chat.slug:
        status_code, response_body = NodeBBClient().categories.delete(
            category_id=team_group_chat.room_id)

        if status_code != 200:
            log.error(
                "Error: Can't delete nodebb team subcategory for the given course %s due to %s",
                instance.course_id,
                response_body
            )
        else:
            team_group_chat.delete()
            log.info("Successfully deleted team subcategory chat for course %s", instance.course_id)
