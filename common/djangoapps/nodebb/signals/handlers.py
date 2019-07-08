from logging import getLogger

from crum import get_current_request
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver

from common.djangoapps.nodebb.tasks import (task_create_user_on_nodebb, task_update_user_profile_on_nodebb,
                                            task_delete_user_on_nodebb, task_activate_user_on_nodebb,
                                            task_join_group_on_nodebb, task_un_join_group_on_nodebb)
from common.lib.nodebb_client.client import NodeBBClient
from lms.djangoapps.onboarding.helpers import COUNTRIES
from certificates.models import GeneratedCertificate
from lms.djangoapps.onboarding.models import (
    UserExtendedProfile, Organization, FocusArea, EmailPreference, )
from lms.djangoapps.teams.models import CourseTeam, CourseTeamMembership
from mailchimp_pipeline.signals.handlers import send_user_info_to_mailchimp, \
     send_user_course_completions_to_mailchimp, send_user_enrollments_to_mailchimp
from nodebb.models import DiscussionCommunity, TeamGroupChat
from common.djangoapps.nodebb.helpers import get_community_id
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.signals.signals import COURSE_CERT_AWARDED

from student.models import ENROLL_STATUS_CHANGE, EnrollStatusChange, UserProfile, CourseEnrollment
from xmodule.modulestore.django import modulestore


log = getLogger(__name__)


def log_action_response(user, status_code, response_body):
    if status_code != 200:
        log.error("Error: Can not update user(%s) on nodebb due to %s" %
                  (user.username, response_body))
    else:
        log.info('Success: User(%s) has been updated on nodebb' %
                 user.username)


@receiver(COURSE_CERT_AWARDED, sender=GeneratedCertificate)
def handle_course_cert_awarded(sender, user, course_key, **kwargs):  # pylint: disable=unused-argument
    data = {"user_id": user.id}
    send_user_course_completions_to_mailchimp.delay(data)


@receiver(post_save, sender=UserProfile)
def sync_user_profile_info_with_nodebb(sender, instance, created, **kwargs):
    city_of_residence = instance.city
    country_of_residence = COUNTRIES.get(instance.country.code, '')
    birth_year = instance.year_of_birth
    language = instance.language

    if not created and (country_of_residence or birth_year or language):
        user = instance.user
        data_to_sync = {
            "city_of_residence": city_of_residence,
            "country_of_residence": country_of_residence,
            "birthday": "01/01/%s" % birth_year,
            "language": language,
        }
        task_update_user_profile_on_nodebb.delay(
            username=user.username, profile_data=data_to_sync)


@receiver(post_save, sender=UserExtendedProfile)
def sync_extended_profile_info_with_nodebb(sender, instance, **kwargs):
    request = get_current_request()
    user = instance.user
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
def sync_organization_info_with_nodebb(sender, instance, created, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """
    Sync information b/w NodeBB User Profile and Edx User Profile
    """

    # To prevent unnecessary API calls in case Django only updates
    # updated_at etc.
    request = get_current_request()
    focus_area = FocusArea.objects.get(code=instance.focus_area).label if instance.focus_area else ''

    # For anonymous user username is empty('') so we can't sync with mailchimp
    if request is None or not focus_area or not request.user.is_anonymous():
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
    send_user_info_to_mailchimp(sender, instance, created, kwargs)

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
        # This sanity blocks two extra syncs because during 'registration'
        # we sync first_name and last_name under above 'created' sanity block
        # so no need to sync first_name and last_name again.
        if 'registration' not in request.path:
            data_to_sync = {
                'first_name': instance.first_name,
                'last_name': instance.last_name
            }

            task_update_user_profile_on_nodebb.delay(
                username=instance.username, profile_data=data_to_sync)



@receiver(post_delete, sender=User)
def delete_user_from_nodebb(sender, **kwargs):
    """
    Delete User from NodeBB when deleted at edx (either deleted via admin-panel OR user is under age)
    """
    instance = kwargs['instance']

    task_delete_user_on_nodebb.delay(username=instance.username)


@receiver(pre_save, sender=User, dispatch_uid='activate_deactivate_user_on_nodebb')
def activate_deactivate_user_on_nodebb(sender, instance, **kwargs):
    """
    Activate or Deactivate a user on nodebb whenever user's active state changes on edx platform
    """
    current_user_obj = User.objects.filter(pk=instance.pk)

    if current_user_obj.first() and current_user_obj[0].is_active != instance.is_active:
        task_activate_user_on_nodebb.delay(
            username=instance.username, active=instance.is_active)


@receiver(post_save, sender=CourseOverview, dispatch_uid="nodebb.signals.handlers.create_category_on_nodebb")
def create_category_on_nodebb(instance, **kwargs):
    """
    Create a community on NodeBB if it's already not exists
    """
    community_exists = DiscussionCommunity.objects.filter(course_id=instance.id).first()

    """
    Following code is to block the double community creation.
    When ever a course created CourseOverviews's post_save triggered twice
    On the base of function call trace we allow one of those whose 5th function
    in trace is '_listen_for_course_publish'
    """
    import inspect
    curframe = inspect.currentframe()
    main_triggerer_function = inspect.getouterframes(curframe)[5][3]

    if not community_exists and main_triggerer_function is '_listen_for_course_publish':
        community_name = '%s-%s-%s-%s' % (instance.display_name,
                                          instance.id.org, instance.id.course, instance.id.run)
        status_code, response_body = NodeBBClient().categories.create(
            name=community_name, label=instance.display_name)

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


@receiver(post_save, sender=CourseEnrollment)
def manage_membership_on_nodebb_group(instance, **kwargs):  # pylint: disable=unused-argument
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
        send_user_enrollments_to_mailchimp(instance.user)


@receiver(pre_delete, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.delete_groupchat_on_nodebb")
def delete_groupchat_on_nodebb(sender, instance, **kwargs):
    """
    Delete group on NodeBB whenever a team is deleted
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if team_group_chat and not team_group_chat.slug:
        status_code, response_body = NodeBBClient().groups.delete(
            room_id=team_group_chat.room_id)

        if status_code != 200:
            log.error(
                "Error: Can't delete nodebb group for the given course %s due to %s" % (
                    instance.course_id, response_body
                )
            )
        else:
            team_group_chat.delete()
            log.info("Successfully deleted group chat for course %s" %
                     instance.course_id)


# TODO: following method is obsolete
@receiver(post_save, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.join_groupchat_on_nodebb")
def join_groupchat_on_nodebb(sender, instance, created, **kwargs):
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
                'Error: Can not join the group, user (%s, %s) due to %s' % (
                    instance.team.name, instance.user, response_body
                )
            )
        else:
            log.info('Success: User have joined the group %s successfully' %
                     instance.team.name)


# TODO: following method is obsolete
@receiver(post_delete, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.leave_groupchat_on_nodebb")
def leave_groupchat_on_nodebb(sender, instance, **kwargs):
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
                'Error: Can not unjoin the group, user (%s, %s) due to %s' % (
                    instance.team.name, instance.user, response_body
                )
            )
        else:
            log.info('Success: User have unjoined the group %s successfully' %
                     instance.team.name)


@receiver(post_save, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.create_update_team_subcategory_on_nodebb")
def create_update_team_subcategory_on_nodebb(sender, instance, created, **kwargs):
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
                "Error: Can't create nodebb subcategory for the given course team %s due to %s" % (
                    instance.name, response_body
                )
            )
        else:
            TeamGroupChat.objects.create(
                team_id=instance.id, slug=response_body['categoryData']['slug'],
                room_id=response_body['categoryData']['cid']
            )
            log.info("Successfully created subcategory for course team %s" %
                     instance.name)
    else:
        # TODO: NodeBB client doesn't have update category method
        pass


def _get_team_subcategory_data(instance):
    subcategory_info = {
        'name': '{}-{}'.format(instance.name, instance.id),
        'label': instance.name,
        'parent_cid': int(get_community_id(instance.course_id))
    }

    return subcategory_info


@receiver(post_save, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.join_team_subcategory_on_nodebb")
def join_team_subcategory_on_nodebb(sender, instance, created, **kwargs):
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
                'Error: Can not join team subcategory, user (%s, %s) due to %s' % (
                    instance.team.name, instance.user.username, response_body
                )
            )
        else:
            log.info('Success: User has joined team subcategory %s successfully' %
                     instance.team.name)


@receiver(post_delete, sender=CourseTeamMembership, dispatch_uid="nodebb.signals.handlers.leave_team_subcategory_on_nodebb")
def leave_team_subcategory_on_nodebb(sender, instance, **kwargs):
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
                'Error: Can not leave team subcategory, user (%s, %s) due to %s' % (
                    instance.team.name, instance.user.username, response_body
                )
            )
        else:
            log.info('Success: User has left team subcategory %s successfully' %
                     instance.team.name)


@receiver(pre_delete, sender=CourseTeam, dispatch_uid="nodebb.signals.handlers.delete_team_subcategory_on_nodebb")
def delete_team_subcategory_on_nodebb(sender, instance, **kwargs):
    """
    Delete team subcategory on NodeBB whenever a team is deleted
    """
    team_group_chat = TeamGroupChat.objects.filter(team_id=instance.id).first()

    if team_group_chat and team_group_chat.slug:
        status_code, response_body = NodeBBClient().categories.delete(
            category_id=team_group_chat.room_id)

        if status_code != 200:
            log.error(
                "Error: Can't delete nodebb team subcategory for the given course %s due to %s" % (
                    instance.course_id, response_body
                )
            )
        else:
            team_group_chat.delete()
            log.info("Successfully deleted team subcategory chat for course %s" %
                     instance.course_id)
