"""Django models related to teams functionality."""

from datetime import datetime
from uuid import uuid4
import pytz
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy
from django_countries.fields import CountryField

from django_comment_common.signals import (
    thread_created,
    thread_edited,
    thread_deleted,
    thread_voted,
    comment_created,
    comment_edited,
    comment_deleted,
    comment_voted,
    comment_endorsed
)
from xmodule_django.models import CourseKeyField
from util.model_utils import generate_unique_readable_id
from student.models import LanguageField, CourseEnrollment
from .errors import AlreadyOnTeamInCourse, NotEnrolledInCourseForTeam
from teams import TEAM_DISCUSSION_CONTEXT


@receiver(thread_voted)
@receiver(thread_created)
@receiver(comment_voted)
@receiver(comment_created)
def post_create_vote_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """Update the user's last activity date upon creating or voting for a
    post."""
    handle_activity(kwargs['user'], kwargs['post'])


@receiver(thread_edited)
@receiver(thread_deleted)
@receiver(comment_edited)
@receiver(comment_deleted)
def post_edit_delete_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """Update the user's last activity date upon editing or deleting a
    post."""
    post = kwargs['post']
    handle_activity(kwargs['user'], post, long(post.user_id))


@receiver(comment_endorsed)
def comment_endorsed_handler(sender, **kwargs):  # pylint: disable=unused-argument
    """Update the user's last activity date upon endorsing a comment."""
    comment = kwargs['post']
    handle_activity(kwargs['user'], comment, long(comment.thread.user_id))


def handle_activity(user, post, original_author_id=None):
    """Handle user activity from django_comment_client and discussion_api
    and update the user's last activity date. Checks if the user who
    performed the action is the original author, and that the
    discussion has the team context.
    """
    if original_author_id is not None and user.id != original_author_id:
        return
    if getattr(post, "context", "course") == TEAM_DISCUSSION_CONTEXT:
        CourseTeamMembership.update_last_activity(user, post.commentable_id)


class CourseTeam(models.Model):
    """This model represents team related info."""

    team_id = models.CharField(max_length=255, unique=True)
    discussion_topic_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    is_active = models.BooleanField(default=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    topic_id = models.CharField(max_length=255, db_index=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=300)
    country = CountryField(blank=True)
    language = LanguageField(
        blank=True,
        help_text=ugettext_lazy("Optional language the team uses as ISO 639-1 code."),
    )
    last_activity_at = models.DateTimeField()
    users = models.ManyToManyField(User, db_index=True, related_name='teams', through='CourseTeamMembership')

    @classmethod
    def create(cls, name, course_id, description, topic_id=None, country=None, language=None):
        """Create a complete CourseTeam object.

        Args:
            name (str): The name of the team to be created.
            course_id (str): The ID string of the course associated
              with this team.
            description (str): A description of the team.
            topic_id (str): An optional identifier for the topic the
              team formed around.
            country (str, optional): An optional country where the team
              is based, as ISO 3166-1 code.
            language (str, optional): An optional language which the
              team uses, as ISO 639-1 code.

        """

        team_id = generate_unique_readable_id(name, cls.objects.all(), 'team_id')
        discussion_topic_id = uuid4().hex

        course_team = cls(
            team_id=team_id,
            discussion_topic_id=discussion_topic_id,
            name=name,
            course_id=course_id,
            topic_id=topic_id if topic_id else '',
            description=description,
            country=country if country else '',
            language=language if language else '',
            last_activity_at=datetime.utcnow().replace(tzinfo=pytz.utc)
        )

        return course_team

    def add_user(self, user):
        """Adds the given user to the CourseTeam."""
        if not CourseEnrollment.is_enrolled(user, self.course_id):
            raise NotEnrolledInCourseForTeam
        if CourseTeamMembership.user_in_team_for_course(user, self.course_id):
            raise AlreadyOnTeamInCourse
        return CourseTeamMembership.objects.create(
            user=user,
            team=self
        )


class CourseTeamMembership(models.Model):
    """This model represents the membership of a single user in a single team."""

    class Meta(object):
        """Stores meta information for the model."""
        unique_together = (('user', 'team'),)

    user = models.ForeignKey(User)
    team = models.ForeignKey(CourseTeam, related_name='membership')
    date_joined = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        """ Customize save method to set the last_activity_at if it does not currently exist. """
        if not self.last_activity_at:
            self.last_activity_at = datetime.utcnow().replace(tzinfo=pytz.utc)

        super(CourseTeamMembership, self).save(*args, **kwargs)

    @classmethod
    def get_memberships(cls, username=None, course_ids=None, team_id=None):
        """
        Get a queryset of memberships.

        Args:
            username (unicode, optional): The username to filter on.
            course_ids (list of unicode, optional) Course IDs to filter on.
            team_id (unicode, optional): The team_id to filter on.
        """
        queryset = cls.objects.all()
        if username is not None:
            queryset = queryset.filter(user__username=username)
        if course_ids is not None:
            queryset = queryset.filter(team__course_id__in=course_ids)
        if team_id is not None:
            queryset = queryset.filter(team__team_id=team_id)

        return queryset

    @classmethod
    def user_in_team_for_course(cls, user, course_id):
        """
        Checks whether or not a user is already in a team in the given course.

        Args:
            user: the user that we want to query on
            course_id: the course_id of the course we're interested in

        Returns:
            True if the user is on a team in the course already
            False if not
        """
        return cls.objects.filter(user=user, team__course_id=course_id).exists()

    @classmethod
    def update_last_activity(cls, user, discussion_topic_id):
        """Set the `last_activity_at` for both this user and their team in the
        given discussion topic. No-op if the user is not a member of
        the team for this discussion.
        """
        try:
            membership = cls.objects.get(user=user, team__discussion_topic_id=discussion_topic_id)
        # If a privileged user is active in the discussion of a team
        # they do not belong to, do not update their last activity
        # information.
        except ObjectDoesNotExist:
            return
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        membership.last_activity_at = now
        membership.team.last_activity_at = now
        membership.team.save()
        membership.save()
