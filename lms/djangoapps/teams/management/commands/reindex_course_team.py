""" Management command to update course_teams' search index. """
from django.core.management import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from optparse import make_option
from textwrap import dedent

from teams.models import CourseTeam


class Command(BaseCommand):
    """
    Command to reindex course_teams (single, multiple or all available).

    Examples:

        ./manage.py reindex_course_team team1 team2 - reindexes course teams with team_ids team1 and team2
        ./manage.py reindex_course_team --all - reindexes all available course teams
    """
    help = dedent(__doc__)

    can_import_settings = True

    args = "<course_team_id course_team_id ...>"

    option_list = BaseCommand.option_list + (
        make_option(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Reindex all course teams'
        ),
    )

    def _get_course_team(self, team_id):
        """ Returns course_team object from team_id. """
        try:
            result = CourseTeam.objects.get(team_id=team_id)
        except ObjectDoesNotExist:
            raise CommandError(u"Argument {0} is not a course_team team_id".format(team_id))

        return result

    def handle(self, *args, **options):
        """
        By convention set by django developers, this method actually executes command's actions.
        So, there could be no better docstring than emphasize this once again.
        """
        # This is ugly, but there is a really strange circular dependency that doesn't
        # happen anywhere else that I can't figure out how to avoid it :(
        from teams.search_indexes import CourseTeamIndexer

        if len(args) == 0 and not options.get('all', False):
            raise CommandError(u"reindex_course_team requires one or more arguments: <course_team_id>")
        elif not settings.FEATURES.get('ENABLE_TEAMS', False):
            raise CommandError(u"ENABLE_TEAMS must be enabled to use course team indexing")

        if options.get('all', False):
            course_teams = CourseTeam.objects.all()
        else:
            course_teams = map(self._get_course_team, args)

        for course_team in course_teams:
            print "Indexing {id}".format(id=course_team.team_id)
            CourseTeamIndexer.index(course_team)
