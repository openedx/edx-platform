"""Factories for testing the Teams API."""

import factory
from factory.django import DjangoModelFactory

from ..models import CourseTeam


class CourseTeamFactory(DjangoModelFactory):
    """Factory for CourseTeams.

    Note that team_id is not auto-generated from name when using the factory.
    """
    FACTORY_FOR = CourseTeam
    FACTORY_DJANGO_GET_OR_CREATE = ('team_id',)

    team_id = factory.Sequence('team-{0}'.format)
    name = "Awesome Team"
    description = "A simple description"
