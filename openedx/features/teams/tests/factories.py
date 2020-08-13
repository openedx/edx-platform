""" Factories Required for testing teams module """
import factory
from factory.django import DjangoModelFactory

from lms.djangoapps.teams.tests.factories import CourseTeamFactory as BaseCourseTeamFactory
from nodebb.models import TeamGroupChat

TEAM_LANGUAGE = 'en'
TEAM_COUNTRY = 'US'


class CourseTeamFactory(BaseCourseTeamFactory):
    """ A custom CourseTeamFactory to generate "TeamGroupChat" along with "CourseTeam" object. """

    country = TEAM_COUNTRY
    language = TEAM_LANGUAGE

    @factory.post_generation
    def team_group_chat(self, create, expected, **kwargs):  # pylint: disable=unused-argument
        """ Create a TeamGroupChat object for the created CourseTeam object
        :class:`factory.declarations.PostGenerationDeclaration`
        """
        if create:
            self.save()
            return TeamGroupChatFactory.create(team=self, room_id=0, **kwargs)
        else:
            return None


class TeamGroupChatFactory(DjangoModelFactory):
    """ Factory for TeamGroupChat model. """
    class Meta(object):
        model = TeamGroupChat
        django_get_or_create = ('slug',)

    slug = factory.Sequence('TeamGroupChat{0}'.format)
