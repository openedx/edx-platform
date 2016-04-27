""" Tests for course_team reindex command """
import ddt
import mock

from mock import patch
from django.core.management import call_command, CommandError
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from common.test.utils import nostderr
from opaque_keys.edx.keys import CourseKey
from teams.tests.factories import CourseTeamFactory
from teams.search_indexes import CourseTeamIndexer
from search.search_engine_base import SearchEngine

COURSE_KEY1 = CourseKey.from_string('edx/history/1')


@ddt.ddt
class ReindexCourseTeamTest(SharedModuleStoreTestCase):
    """Tests for the ReindexCourseTeam command"""

    def setUp(self):
        """
        Set up tests.
        """
        super(ReindexCourseTeamTest, self).setUp()

        self.team1 = CourseTeamFactory(course_id=COURSE_KEY1, team_id='team1')
        self.team2 = CourseTeamFactory(course_id=COURSE_KEY1, team_id='team2')
        self.team3 = CourseTeamFactory(course_id=COURSE_KEY1, team_id='team3')

        self.search_engine = SearchEngine.get_search_engine(index='index_course_team')

    def test_given_no_arguments_raises_command_error(self):
        """ Test that raises CommandError for incorrect arguments. """
        with self.assertRaises(SystemExit), nostderr():
            with self.assertRaisesRegexp(CommandError, ".* requires one or more arguments .*"):
                call_command('reindex_course_team')

    def test_teams_search_flag_disabled_raises_command_error(self):
        """ Test that raises CommandError for disabled feature flag. """
        with mock.patch('django.conf.settings.FEATURES') as features:
            features.return_value = {"ENABLE_TEAMS": False}
            with self.assertRaises(SystemExit), nostderr():
                with self.assertRaisesRegexp(CommandError, ".* ENABLE_TEAMS must be enabled .*"):
                    call_command('reindex_course_team')

    def test_given_invalid_team_id_raises_command_error(self):
        """ Test that raises CommandError for invalid team id. """
        with self.assertRaises(SystemExit), nostderr():
            with self.assertRaisesRegexp(CommandError, ".* Argument {0} is not a course_team id .*"):
                call_command('reindex_course_team', u'team4')

    @patch.object(CourseTeamIndexer, 'index')
    def test_single_team_id(self, mock_index):
        """ Test that command indexes a single passed team. """
        call_command('reindex_course_team', self.team1.team_id)
        mock_index.assert_called_once_with(self.team1)
        mock_index.reset_mock()

    @patch.object(CourseTeamIndexer, 'index')
    def test_multiple_team_id(self, mock_index):
        """ Test that command indexes multiple passed teams. """
        call_command('reindex_course_team', self.team1.team_id, self.team2.team_id)
        mock_index.assert_any_call(self.team1)
        mock_index.assert_any_call(self.team2)
        mock_index.reset_mock()

    @patch.object(CourseTeamIndexer, 'index')
    def test_all_teams(self, mock_index):
        """ Test that command indexes all teams. """
        call_command('reindex_course_team', all=True)
        mock_index.assert_any_call(self.team1)
        mock_index.assert_any_call(self.team2)
        mock_index.assert_any_call(self.team3)
        mock_index.reset_mock()
