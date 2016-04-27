"""Factories for testing the Teams API."""

import pytz
from datetime import datetime
from uuid import uuid4

import factory
from factory.django import DjangoModelFactory

from ..models import CourseTeam, CourseTeamMembership


LAST_ACTIVITY_AT = datetime(2015, 8, 15, 0, 0, 0, tzinfo=pytz.utc)


class CourseTeamFactory(DjangoModelFactory):
    """Factory for CourseTeams.

    Note that team_id is not auto-generated from name when using the factory.
    """
    class Meta(object):
        model = CourseTeam
        django_get_or_create = ('team_id',)

    team_id = factory.Sequence('team-{0}'.format)
    discussion_topic_id = factory.LazyAttribute(lambda a: uuid4().hex)
    name = factory.Sequence("Awesome Team {0}".format)
    description = "A simple description"
    last_activity_at = LAST_ACTIVITY_AT


class CourseTeamMembershipFactory(DjangoModelFactory):
    """Factory for CourseTeamMemberships."""
    class Meta(object):
        model = CourseTeamMembership

    last_activity_at = LAST_ACTIVITY_AT

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create the team membership. """
        obj = model_class(*args, **kwargs)
        obj.save()
        return obj
