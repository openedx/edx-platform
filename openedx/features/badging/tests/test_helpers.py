"""
Unit tests for badging helpers
"""
import factory
import mock
from django.db.models import signals

from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from nodebb.constants import CONVERSATIONALIST_ENTRY_INDEX, TEAM_PLAYER_ENTRY_INDEX
from openedx.features.badging.constants import CONVERSATIONALIST, TEAM_PLAYER
from openedx.features.badging.helpers import badges as badge_helpers
from openedx.features.badging.helpers import notifications as notification_helpers
from openedx.features.teams.tests.factories import TeamGroupChatFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..handlers import register_notification_types
from ..models import Badge
from .factories import BadgeFactory, UserBadgeFactory


class BadgeHelperTestCases(ModuleStoreTestCase):
    """
    Unit tests for badging helpers
    """

    def setUp(self):
        super(BadgeHelperTestCases, self).setUp()
        self.user = UserFactory()
        self.course1 = CourseFactory(org="test1", number="123", run="1", display_name="ABC")
        self.type_conversationalist = CONVERSATIONALIST[CONVERSATIONALIST_ENTRY_INDEX]  # badge type

    def test_populate_trophycase_with_empty_course_list(self):
        """
        For empty course list, trophy case should not return any data except empty dictionary
        :return: None
        """
        trophycase_dict = badge_helpers.populate_trophycase(user=self.user, courses=list(), earned_badges=mock.ANY)
        self.assertEqual(trophycase_dict, dict())

    def test_populate_trophycase_with_courses_none(self):
        """
        If course list is None, trophy case should throw error
        :return: None
        """
        with self.assertRaises(TypeError):
            badge_helpers.populate_trophycase(user=self.user, courses=None, earned_badges=mock.ANY)

    @mock.patch('openedx.features.badging.helpers.badges.get_course_badges')
    def test_populate_trophycase_successful_and_ordered_by_course_name(self, mock_get_course_badges):
        """
        For a list of courses, trophy case should return data sorted by course name
        :param mock_get_course_badges: mock return value for course badges
        :return: None
        """
        mock_get_course_badges.return_value = {"badges": 'mocked badges'}

        course2 = CourseFactory(org="test2", number="123", run="1", display_name="XYZ")
        course3 = CourseFactory(org="test3", number="123", run="1", display_name="Course3")
        CourseFactory(org="test4", number="123", run="1", display_name="Course4")

        # Enroll in three courses, two active and one inactive
        CourseEnrollmentFactory(user=self.user, course_id=self.course1.id, is_active=True)
        CourseEnrollmentFactory(user=self.user, course_id=course2.id, is_active=True)
        CourseEnrollmentFactory(user=self.user, course_id=course3.id, is_active=False)

        courses = [
            (self.course1.id, self.course1.display_name),
            (course2.id, course2.display_name)
        ]
        trophycase_dict = badge_helpers.populate_trophycase(self.user, courses, earned_badges=mock.ANY)

        expected_return_value = dict([
            (u'test1/123/1', {'display_name': u'ABC', 'badges': 'mocked badges'}),
            (u'test2/123/1', {'display_name': u'XYZ', 'badges': 'mocked badges'})
        ])

        self.assertEqual(expected_return_value, trophycase_dict)

        # assert order of courses by display name
        course_detail = trophycase_dict.values()
        self.assertEqual(expected_return_value['test1/123/1'], course_detail[0])
        self.assertEqual(expected_return_value['test2/123/1'], course_detail[1])

    @mock.patch('openedx.features.badging.helpers.badges.Badge.objects.all')
    def test_get_course_badges_with_empty_badge_queryset(self, mock_badge_objects_all):
        """
        Testing optional parameter badge_queryset. If it is None or not passed to function, it
        should be created from inside
        :param mock_badge_objects_all: mocking query set & generating fake exception, just to assert on it
        :return: None
        """
        message = 'Raising fake exception, if badge_queryset is none'
        mock_badge_objects_all.side_effect = Exception(message)

        with self.assertRaises(Exception) as error:
            badge_helpers.get_course_badges(user=self.user, course_id=mock.ANY, earned_badges=mock.ANY,
                                            badge_queryset=Badge.objects.none())

        self.assertEqual(str(error.exception), message)

    @mock.patch('openedx.features.badging.helpers.badges.add_badge_earned_date')
    @mock.patch('openedx.features.badging.helpers.badges.filter_earned_badge_by_joined_team')
    @mock.patch('openedx.features.badging.helpers.badges.is_teams_feature_enabled')
    @mock.patch('openedx.features.badging.helpers.badges.get_course_by_id')
    def test_get_course_badges_successfully(
        self,
        mock_get_course_by_id,
        mock_is_teams_feature_enabled,
        mock_filter_earned_badge_by_joined_team,
        mock_add_badge_earned_date  # pylint: disable=unused-argument
    ):
        """
        Create 1 course, 3 badges (1 team, 2 conversationalist), none of the badges are earned, to test success case
        :param mock_get_course_by_id: mock course id, because it is irrelevant here
        :param mock_is_teams_feature_enabled: mock and return False to disable teams feature
        :param mock_filter_earned_badge_by_joined_team: mock such that user has no joined team and no earned badge
        :param mock_add_badge_earned_date: mock and return nothing, since there is no earned badge
        :return: None
        """
        mock_get_course_by_id.return_value = mock.ANY
        mock_is_teams_feature_enabled.return_value = False
        mock_filter_earned_badge_by_joined_team.return_value = False, list()

        BadgeFactory(type=TEAM_PLAYER[TEAM_PLAYER_ENTRY_INDEX], threshold=2)
        badge2 = BadgeFactory(type=self.type_conversationalist, threshold=2)
        badge3 = BadgeFactory(type=self.type_conversationalist, threshold=5)

        badges = badge_helpers.get_course_badges(self.user, self.course1.id, earned_badges=mock.ANY)

        expected_result = {
            'badges': {
                'conversationalist': [{
                    'image': badge2.image,
                    'color_image': u'',
                    'congrats_message': u'',
                    'threshold': 2,
                    'date_created': badge2.date_created,
                    'type': u'conversationalist',
                    u'id': badge2.id,
                    'name': badge2.name
                }, {
                    'image': badge3.image,
                    'color_image': u'',
                    'congrats_message': u'',
                    'threshold': 5,
                    'date_created': badge3.date_created,
                    'type': u'conversationalist',
                    u'id': badge3.id,
                    'name': badge3.name
                }]
            }
        }

        self.assertEqual(expected_result, badges)

        expected_conversationalist_badges = expected_result['badges']['conversationalist']
        self.assertEqual(expected_conversationalist_badges[0]['threshold'], badge2.threshold)
        self.assertEqual(expected_conversationalist_badges[1]['threshold'], badge3.threshold)

        badge_keys = badges['badges'].keys()
        self.assertIn('conversationalist', badge_keys)
        self.assertNotIn('team', badge_keys)

    @mock.patch('openedx.features.badging.helpers.badges.add_badge_earned_date')
    @mock.patch('openedx.features.badging.helpers.badges.filter_earned_badge_by_joined_team')
    @mock.patch('openedx.features.badging.helpers.badges.is_teams_feature_enabled')
    @mock.patch('openedx.features.badging.helpers.badges.get_course_by_id')
    def test_get_course_badges_user_not_joined_any_course_team(
        self,
        mock_get_course_by_id,
        mock_is_teams_feature_enabled,
        mock_filter_earned_badge_by_joined_team,
        mock_add_badge_earned_date  # pylint: disable=unused-argument
    ):
        """
        Create 1 course, 1 conversationalist badge, to test course badges, when team feature is enabled but user
        has not joined any team in a course
        :param mock_get_course_by_id: mock course id, because it is irrelevant here
        :param mock_is_teams_feature_enabled: mock and return True to enable teams feature
        :param mock_filter_earned_badge_by_joined_team: mock such that user has no joined team and no earned badge
        :param mock_add_badge_earned_date: mock and return nothing, since there is no earned badge
        :return: None
        """
        mock_get_course_by_id.return_value = mock.ANY
        mock_is_teams_feature_enabled.return_value = True
        mock_filter_earned_badge_by_joined_team.return_value = False, list()

        badge = BadgeFactory(type=self.type_conversationalist, threshold=2)

        badges = badge_helpers.get_course_badges(self.user, self.course1.id, earned_badges=mock.ANY)

        expected_result = {
            'badges': {
                'conversationalist': [{
                    'image': badge.image,
                    'color_image': u'',
                    'congrats_message': u'',
                    'threshold': 2,
                    'date_created': badge.date_created,
                    'type': u'conversationalist',
                    u'id': badge.id,
                    'name': badge.name
                }],
                'team': []
            }
        }

        self.assertEqual(expected_result, badges)

    def test_add_badge_earned_date_no_course_badges(self):
        """
        Assert that exception is raised when adding badge earned date, if provided course badges are None
        :return: None
        """
        with self.assertRaises(TypeError):
            badge_helpers.add_badge_earned_date(self.course1.id, course_badges=None, earned_badges=mock.ANY)

    def test_add_badge_earned_date_no_earned_badges(self):
        """
        Assert that exception is raised when adding badge earned date, if no earned badge exists for
        provided course badges
        :return: None
        """
        badge = BadgeFactory(threshold=2)
        course_badges = [badge, ]
        with self.assertRaises(TypeError):
            badge_helpers.add_badge_earned_date(self.course1.id, course_badges, earned_badges=None)

    def test_add_badge_earned_date_earned_badges_in_different_courses(self):
        """
        Create 2 badges, 2 courses and assign one badge per course respectively. Assert that earned date will
        be added to only that badge whose course id will match with course id provided (in param)
        :return: None
        """
        course2 = CourseFactory(org="test2", number="123", run="1", display_name="XYZ")

        badge1 = BadgeFactory(threshold=2)
        badge2 = BadgeFactory(threshold=5)

        user_badge_1 = UserBadgeFactory(user=self.user, course_id=self.course1.id, badge=badge1)
        user_badge_2 = UserBadgeFactory(user=self.user, course_id=course2.id, badge=badge2)

        course_badges = list(
            Badge.objects.all().values()
        )
        earned_badges = [user_badge_1, user_badge_2]
        badge_helpers.add_badge_earned_date(self.course1.id, course_badges, earned_badges)

        # get badges by index, since list maintains insertion order
        self.assertIsNotNone(course_badges[0]['date_earned'])
        self.assertRaises(KeyError, lambda: course_badges[1]['date_earned'])

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_filter_earned_badge_by_joined_team(self):
        """
        Create team in course and add user in it. Create 2 badges, both earned by user in a course but in two
        different teams, one of which user is currently part of. Assert that currently joined team exists and
        user has earned right number of right badges in that team
        :return: None
        """
        badge1 = BadgeFactory(threshold=2)
        badge2 = BadgeFactory(threshold=12)
        user_badge1 = UserBadgeFactory(user=self.user, course_id=self.course1.id, badge=badge1, community_id=100)
        user_badge2 = UserBadgeFactory(user=self.user, course_id=self.course1.id, badge=badge2, community_id=101)

        earned_badges = [user_badge1, user_badge2]

        course_team_from_factory = CourseTeamFactory(course_id=self.course1.id, team_id='team1')
        CourseTeamMembershipFactory(user=self.user, team=course_team_from_factory)
        TeamGroupChatFactory(team=course_team_from_factory, room_id=100)

        course_team, earned_badges = badge_helpers.filter_earned_badge_by_joined_team(
            self.user, self.course1, earned_badges)

        self.assertIsNotNone(course_team)
        self.assertEqual(earned_badges, [user_badge1])

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def test_filter_earned_badge_by_joined_team_invalid_room_id(self):
        """
        For a course, in which user is part of a team, which has invalid room it, Assert that exception is raised
        due to invalid room id
        :return: None
        """
        course_team_from_factory = CourseTeamFactory(course_id=self.course1.id, team_id='team1')
        CourseTeamMembershipFactory(user=self.user, team=course_team_from_factory)

        with self.assertRaises(Exception):
            badge_helpers.filter_earned_badge_by_joined_team(self.user, self.course1, earned_badges=mock.ANY)

    def test_filter_earned_badge_by_joined_team_course_with_no_team(self):
        """
        For a course in which user has not joined any team, Assert that course team is None
        and earned badge list is empty
        :return: None
        """
        course_team, earned_badges = badge_helpers.filter_earned_badge_by_joined_team(
            self.user, self.course1, earned_badges=mock.ANY)

        self.assertIsNone(course_team)
        self.assertEqual(earned_badges, list())

    @mock.patch('openedx.features.badging.helpers.notifications.render_to_string')
    @mock.patch('openedx.features.badging.helpers.notifications.publish_notification_to_user')
    def test_send_user_badge_notification(self, mock_publish_notification_to_user,
                                          mock_render_to_string):
        """
        Test newly earned badge notification is sent to user
        :param mock_publish_notification_to_user: mock and send notification through edx_notifications
        :param mock_render_to_string: mock and return message body that appear in notification
        :return: None
        """
        # register badge notification type
        register_notification_types(None)
        mock_render_to_string.return_value = 'You have earned a new badge:<br><strong>newly_earned_badge_name</strong>'

        notification_helpers.send_user_badge_notification(self.user, 'dummy_badge_url', 'newly_earned_badge_name')

        expected_context = {
            'badge_name': 'newly_earned_badge_name'
        }

        mock_render_to_string.assert_called_once_with('philu_notifications/templates/user_badge_earned.html',
                                                      expected_context)

        mock_publish_notification_to_user.assert_called_once_with(self.user.id, mock.ANY)
