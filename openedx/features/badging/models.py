from django.contrib.auth.models import User
from django.db import models

from lms.djangoapps.teams.models import CourseTeamMembership
from nodebb.constants import (
    COMMUNITY_ID_SPLIT_INDEX,
    TEAM_PLAYER_ENTRY_INDEX,
    CONVERSATIONALIST_ENTRY_INDEX
)
from nodebb.helpers import get_course_id_by_community_id
from nodebb.models import TeamGroupChat
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField

from .constants import CONVERSATIONALIST, TEAM_PLAYER


class Badge(models.Model):
    BADGE_TYPES = (
        CONVERSATIONALIST,
        TEAM_PLAYER
    )

    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField(blank=True, null=True)
    threshold = models.IntegerField(blank=False, null=False)
    type = models.CharField(max_length=100, blank=False, null=False, choices=BADGE_TYPES)
    image = models.CharField(max_length=255, blank=False, null=False)
    date_created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def get_unearned_badges(cls, user_id, community_id, community_type):
        """ Get dictionary of badges that can still be earned in a
            community by a user


            Parameters
            ----------
            user_id : long
                      user id of a user object
            community_id : str
                      community ID of a discussion group
            community_type : str
                      community type string (team/conversationalist)

            Returns
            -------
            Dict
                nested dictionary object of unattained badge information
        """
        latest_earned = UserBadge.objects.filter(user_id=user_id,
                                                 community_id=community_id,
                                                 badge_id__type=community_type).order_by('date_earned').last()

        if latest_earned:
            latest_threshold = Badge.objects.get(pk=latest_earned.badge_id, type=community_type).threshold
            unearned_badges = Badge.objects.filter(type=community_type) \
                                           .exclude(threshold__lte=latest_threshold) \
                                           .order_by('threshold')
        else:
            unearned_badges = Badge.objects.filter(type=community_type).order_by('threshold')

        unearned_badges_dict = {}
        for badge in unearned_badges:
            unearned_badges_dict[badge.id] = {'name': badge.name,
                                              'description': badge.description,
                                              'threshold': badge.threshold,
                                              'type': badge.type,
                                              'image': badge.image}
        return unearned_badges_dict


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
    course_id = CourseKeyField(max_length=255, db_index=True, db_column='course_id', null=False)
    community_id = models.IntegerField(blank=False, null=False, db_column='community_id')
    date_earned = models.DateTimeField(auto_now=True)

    class Meta:
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
        course_id = get_course_id_by_community_id(community_id)
        is_team_badge = True if course_id is CourseKeyField.Empty else False

        try:
            badge_type = Badge.objects.get(id=badge_id).type
        except:
            raise Exception('There exists no badge with id {}'.format(badge_id))

        # Check if the right badge is being awarded in the right community
        if badge_type == CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX] and is_team_badge or \
           badge_type == TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX] and not is_team_badge:
            raise Exception('Badge {} is a {} badge, wrong community'.format(badge_id, badge_type))

        if is_team_badge:
            team = TeamGroupChat.objects.filter(room_id=community_id).exclude(slug='').first()

            if(not team):
                raise Exception('No discussion community or team with id {}'.format(community_id))

            all_team_members = CourseTeamMembership.objects.filter(team_id=team.team_id)

            for member in all_team_members:
                UserBadge.objects.get_or_create(
                    user_id=member.user_id,
                    badge_id=badge_id,
                    course_id=course_id,
                    community_id=community_id
                )
        else:
            UserBadge.objects.get_or_create(
                user_id=user_id,
                badge_id=badge_id,
                course_id=course_id,
                community_id=community_id
            )
