"""
Models to store user and team badges.
"""
import logging

from django.contrib.auth.models import User
from django.db import models, transaction
from rest_framework.renderers import JSONRenderer

from lms.djangoapps.teams.models import CourseTeamMembership
from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX, TEAM_PLAYER_ENTRY_INDEX
from nodebb.helpers import get_course_id_by_community_id
from nodebb.models import TeamGroupChat
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

from . import constants as badge_constants
from .tasks import task_user_badge_notify

log = logging.getLogger('edx.badging')


class BadgeManager(models.Manager):
    """Custom manager for retrieving badges"""

    def get_badges_json(self, badge_type):
        """
        Get json of all badges of provided badge type

        Parameters
        ----------
        badge_type: str
                        badge type string (team/conversationalist)

        Returns
        -------
        JSON
            json of all badges
        """
        badges = Badge.objects.filter(type=badge_type).order_by('threshold').values()
        return JSONRenderer().render(badges)


class Badge(models.Model):
    """
    This stores the badge information
    """
    BADGE_TYPES = (
        badge_constants.CONVERSATIONALIST,
        badge_constants.TEAM_PLAYER
    )

    name = models.CharField(max_length=255)
    congrats_message = models.TextField(default='')
    threshold = models.PositiveIntegerField()
    type = models.CharField(max_length=100, choices=BADGE_TYPES)
    image = models.CharField(max_length=255)
    color_image = models.CharField(max_length=255, default='')
    date_created = models.DateTimeField(auto_now=True)

    objects = BadgeManager()

    class Meta:
        app_label = 'badging'
        unique_together = ('type', 'threshold')
        ordering = ('type', 'threshold')

    def __unicode__(self):
        return self.name


class UserBadge(models.Model):
    """
    Model representing what badges are assigned to which users in communities (both course and team communities).

    Each object of this model represents the assignment of one badge (specified
    by the `badge_id` foreign key) to a certain user (specified by the `user`
    foreign key) in a `community`. Each `community` is related to a course
    which is specified by the `course_id`. A certain badge is only awarded once
    in a community, the unique_together constraint in Meta class makes sure
    that there are no duplicate objects in the model.
    """

    user = models.ForeignKey(User, db_index=True, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    course_id = CourseKeyField(blank=False, max_length=255, db_index=True, db_column='course_id', null=False)
    community_id = models.IntegerField(db_column='community_id')
    date_earned = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'badging'
        unique_together = ('user', 'badge', 'course_id', 'community_id')

    def __unicode__(self):
        return 'User: {user_id}, Badge: {badge_id}'.format(user_id=self.user.id, badge_id=self.badge.id)

    @classmethod
    def assign_badge(cls, user_id, badge_id, community_id):
        """
        Create UserBadge entry, for a specific badge assignment to user(s) in community.

        Parameters
        ----------
        user_id : long
                  user id of a user object
        badge_id : long
                  badge ID of specifying the object in Badge model
        community_id : str
                  community ID of a discussion group

        Returns
        -------
        True: if user badge assigned to all team members in team or for current user in course community
        False: if user badges is already created to any user
        """
        try:
            badge_to_assign = Badge.objects.get(id=badge_id)
            badge_type, badge_name = badge_to_assign.type, badge_to_assign.name
        except Badge.DoesNotExist:
            error = badge_constants.BADGE_NOT_FOUND_ERROR.format(badge_id=badge_id)
            raise Exception(error)

        if badge_type == badge_constants.TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX]:
            team_group_chat = TeamGroupChat.objects.filter(
                room_id=community_id).exclude(slug='').values('team_id', 'team__course_id').first()

            if not team_group_chat:
                error = badge_constants.INVALID_TEAM_ERROR.format(badge_id=badge_id, community_id=community_id)
                raise Exception(error)

            course_id = team_group_chat['team__course_id']

            if not course_id or course_id == CourseKeyField.Empty:
                error = badge_constants.UNKNOWN_COURSE_ERROR.format(badge_id=badge_id, community_id=community_id)
                raise Exception(error)

            all_team_members = CourseTeamMembership.objects.filter(team_id=team_group_chat['team_id'])
            members_with_user_badge = []

            try:
                with transaction.atomic():
                    for member in all_team_members:
                        # assign badge to all team members
                        _, created = UserBadge.objects.get_or_create(
                            user_id=member.user.id,
                            badge_id=badge_id,
                            course_id=course_id,
                            community_id=community_id
                        )
                        if created:
                            # keep track of members, to send email and notification
                            members_with_user_badge.append(member)
            except Exception:
                log.exception(badge_constants.BADGE_ASSIGNMENT_ERROR.format(
                    num_of=len(members_with_user_badge),
                    team_id=community_id
                ))
                raise

            for member in members_with_user_badge:
                # send email and notification to team members who have earned badge
                task_user_badge_notify(member.user, course_id, badge_name)

            # return true only if badge is assigned to all team members
            return len(members_with_user_badge) == len(all_team_members)

        elif badge_type == badge_constants.CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]:
            course_id = get_course_id_by_community_id(community_id)

            if not course_id or course_id == CourseKeyField.Empty:
                error = badge_constants.INVALID_COMMUNITY_ERROR.format(badge_id=badge_id, community_id=community_id)
                raise Exception(error)

            user_badge, created = UserBadge.objects.get_or_create(
                user_id=user_id,
                badge_id=badge_id,
                course_id=course_id,
                community_id=community_id
            )

            if created:
                # send email and notification to user who have earned conversationalist badge
                task_user_badge_notify(user_badge.user, course_id, badge_name)

            return created  # return true only if badge is assigned
        else:
            error = badge_constants.BADGE_TYPE_ERROR.format(badge_id=badge_id, badge_type=badge_type)
            raise Exception(error)

    @classmethod
    def assign_missing_team_badges(cls, user_id, team_id):
        """
        Assign all previous (missing) badges when user joins a team.

        Assign badge such that he has same number of badges as any other member of same team
        """
        if not (user_id and team_id):
            error = badge_constants.TEAM_BADGE_ERROR.format(user_id=user_id, team_id=team_id)
            raise Exception(error)

        team_group_chat = TeamGroupChat.objects.filter(team_id=team_id).values(badge_constants.ROOM_ID_KEY).first()

        # The query gathers the badges earned by the team in a specific course while making sure that duplicate data is
        # not returned, as one badge can be earned by multiple members of the team, hence the distinct keyword.
        earned_team_badges = UserBadge.objects.filter(community_id=team_group_chat[badge_constants.ROOM_ID_KEY]).values(
            badge_constants.BADGE_ID_KEY,
            badge_constants.COURSE_ID_KEY,
            badge_constants.THRESHOLD_KEY).distinct()

        # assign team's earned badges to current user which are not already earned
        for user_badge in earned_team_badges:

            # assign badge to current user
            UserBadge.objects.get_or_create(
                user_id=user_id,
                badge_id=user_badge[badge_constants.BADGE_ID_KEY],
                course_id=user_badge[badge_constants.COURSE_ID_KEY],
                community_id=team_group_chat[badge_constants.ROOM_ID_KEY]
            )
