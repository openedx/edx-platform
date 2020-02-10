import logging

from django.contrib.auth.models import User
from django.db import models
from rest_framework.renderers import JSONRenderer

from lms.djangoapps.teams.models import CourseTeamMembership
from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX, TEAM_PLAYER_ENTRY_INDEX
from nodebb.helpers import get_course_id_by_community_id
from nodebb.models import TeamGroupChat
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

from . import constants as badge_constants

log = logging.getLogger('edx.badging')


class Badge(models.Model):
    BADGE_TYPES = (
        badge_constants.CONVERSATIONALIST,
        badge_constants.TEAM_PLAYER
    )

    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    threshold = models.IntegerField(blank=False, null=False)
    type = models.CharField(max_length=100, blank=False, null=False, choices=BADGE_TYPES)
    image = models.CharField(max_length=255, blank=False, null=False)
    date_created = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'badging'

    def __unicode__(self):
        return self.name

    @classmethod
    def get_badges_json(cls, badge_type):
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


class UserBadge(models.Model):
    """
        This model represents what badges are assigned to which users in
        communities (both course and team communities)

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
    community_id = models.IntegerField(blank=False, null=False, db_column='community_id')
    date_earned = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'badging'
        unique_together = ('user', 'badge', 'course_id', 'community_id')

    def __unicode__(self):
        return 'User: {}, Badge: {}'.format(self.user.id, self.badge.id)

    @classmethod
    def assign_badge(cls, user_id, badge_id, community_id):
        """ Save an entry in the UserBadge table specifying a
            specific badge assignment to a user badge in community

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
            None
        """
        try:
            badge_type = Badge.objects.get(id=badge_id).type
        except:
            error = badge_constants.BADGE_NOT_FOUND_ERROR.format(badge_id=badge_id)
            log.exception(error)
            raise Exception(error)

        if badge_type == badge_constants.TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX]:
            team_group_chat = TeamGroupChat.objects.filter(
                room_id=community_id).exclude(slug='').values('team_id', 'team__course_id').first()

            if not team_group_chat:
                error = badge_constants.INVALID_TEAM_ERROR.format(badge_id=badge_id, community_id=community_id)
                log.exception(error)
                raise Exception(error)

            course_id = team_group_chat['team__course_id']

            if not course_id or course_id == CourseKeyField.Empty:
                error = badge_constants.UNKNOWN_COURSE_ERROR.format(badge_id=badge_id, community_id=community_id)
                log.exception(error)
                raise Exception(error)

            all_team_members = CourseTeamMembership.objects.filter(team_id=team_group_chat['team_id'])
            for member in all_team_members:
                UserBadge.objects.get_or_create(
                    user_id=member.user_id,
                    badge_id=badge_id,
                    course_id=course_id,
                    community_id=community_id
                )
        elif badge_type == badge_constants.CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]:
            course_id = get_course_id_by_community_id(community_id)

            if not course_id or course_id == CourseKeyField.Empty:
                error = badge_constants.INVALID_COMMUNITY_ERROR.format(badge_id=badge_id, community_id=community_id)
                log.exception(error)
                raise Exception(error)

            UserBadge.objects.get_or_create(
                user_id=user_id,
                badge_id=badge_id,
                course_id=course_id,
                community_id=community_id
            )
        else:
            error = badge_constants.BADGE_TYPE_ERROR.format(badge_id=badge_id, badge_type=badge_type)
            log.exception(error)
            raise Exception(error)

    @classmethod
    def assign_missing_team_badges(cls, user_id, team_id):
        """
        Assign all previous (missing) badges when user joins a team,
        such that he has same number of badges as any other member
        of same team
        """
        if not (user_id and team_id):
            error = badge_constants.TEAM_BADGE_ERROR.format(user_id=user_id, team_id=team_id)
            log.exception(error)
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
            UserBadge.objects.get_or_create(
                user_id=user_id,
                badge_id=user_badge[badge_constants.BADGE_ID_KEY],
                course_id=user_badge[badge_constants.COURSE_ID_KEY],
                community_id=team_group_chat[badge_constants.ROOM_ID_KEY]
            )
