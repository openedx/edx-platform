"""
Unit tests for badging views
"""
import mock
from django.core.urlresolvers import reverse

from lms.djangoapps.onboarding.tests.factories import UserFactory
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField
from openedx.core.djangolib.testing.philu_utils import clear_philu_theme, configure_philu_theme
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .factories import BadgeFactory, UserBadgeFactory


class BadgeViewsTestCases(ModuleStoreTestCase):
    """
    Unit tests for badging views
    """

    def setUp(self):
        super(BadgeViewsTestCases, self).setUp()
        self.course = CourseFactory(org="test", number="123", run="1")
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='test')

    @classmethod
    def setUpClass(cls):
        super(BadgeViewsTestCases, cls).setUpClass()
        configure_philu_theme()

    @classmethod
    def tearDownClass(cls):
        clear_philu_theme()
        super(BadgeViewsTestCases, cls).tearDownClass()

    def test_trophycase(self):
        """
        Assert that response code is 200
        :return: None
        """
        response = self.client.get(reverse('trophycase'), follow=True)
        self.assertEqual(response.status_code, 200)

    @mock.patch('openedx.features.badging.views.populate_trophycase')
    def test_trophycase_with_some_earned_badges(self, mock_populate_trophycase):
        """
        Test trophy case for 2 badges, one badge earned by current user and both badges earned by some other user.
        Assert that request is fetching data for only current logged in user for the badges only he has earned
        in relevant course. And Badge earned by other user are ignored
        :param mock_populate_trophycase: mock to assert it has been called with expected input
        :return: None
        """
        badge1 = BadgeFactory()
        badge2 = BadgeFactory(threshold=11)

        # Assign one badge to current user
        user_badge = UserBadgeFactory(user=self.user, badge=badge1)
        # Assign few badge to any other users
        any_other_user = UserFactory()
        UserBadgeFactory(user=any_other_user, course_id=user_badge.course_id, badge=badge1)
        UserBadgeFactory(user=any_other_user, course_id=CourseKeyField.Empty, badge=badge2)

        mock_populate_trophycase.return_value = dict()
        response = self.client.get(reverse('trophycase'), data={'json': True}, follow=True)
        self.assertEqual(response.status_code, 200)
        mock_populate_trophycase.assert_called_once_with(self.user, mock.ANY, [user_badge])

    def test_my_badges_denies_anonymous(self):
        """
        This method test API call without logged-in user. In this case user must be redirected
        to login page
        :return: None
        """
        self.client.logout()
        path = reverse('my_badges', kwargs={'course_id': 'course/123/1'})
        response = self.client.get(path=path)
        self.assertRedirects(response, '{}?next={}'.format(reverse('signin_user'), path))

    def test_trophycase_denies_anonymous(self):
        """
        This method test API call without logged-in user. In this case user must be redirected
        to login page
        :return: None
        """
        self.client.logout()
        path = reverse('trophycase')
        response = self.client.get(path=path)
        self.assertRedirects(response, '{}?next={}'.format(reverse('signin_user'), path))

    def test_my_badges_invalid_course_id(self):
        """
        Test my badges with invalid course id. Assert that an error is raised
        :return: None
        """
        course_id = 'test/course/123'
        path = reverse('my_badges', kwargs={'course_id': course_id})
        response = self.client.get(path, follow=True)
        self.assertEqual(response.status_code, 404)

    @mock.patch('openedx.features.badging.views.get_course_badges')
    def test_my_badges_with_enrolled_and_active_course(self, mock_get_course_badges):
        """
        Test my badges with 1 active course enrollment for valid course
        :param mock_get_course_badges: mock to assert it has been called with expected input
        :return: None
        """
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, is_active=True)

        mock_get_course_badges.return_value = dict()
        response = self.client.get(reverse('my_badges', kwargs={'course_id': self.course.id}))
        self.assertEqual(response.status_code, 200)
        mock_get_course_badges.assert_called_once_with(self.user, self.course.id, list())

    def test_my_badges_with_enrolled_but_inactive_course(self):
        """
        Test my badges with inactive course. Assert that an error is raised
        :return: None
        """
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, is_active=False)

        path = reverse('my_badges', kwargs={'course_id': self.course.id})
        response = self.client.get(path, follow=True)
        self.assertEqual(response.status_code, 404)

    @mock.patch('openedx.features.badging.views.get_course_badges')
    def test_my_badges_with_some_earned_badges(self, mock_get_course_badges):
        """
        Test my badges for 2 badges, one badge earned by current user and both badges earned by some other user.
        Assert that request is fetching data for only current logged in user for the badges only he has earned
        in relevant course. And Badge earned by other user are ignored
        :param mock_get_course_badges: mock to assert it has been called with expected input
        :return: None
        """
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id, is_active=True)

        badge1 = BadgeFactory()
        badge2 = BadgeFactory(threshold=11)

        # Assign one badge to current user
        user_badge = UserBadgeFactory(user=self.user, course_id=self.course.id, badge=badge1)
        # Assign few badge to any other users
        any_other_user = UserFactory()
        UserBadgeFactory(user=any_other_user, course_id=self.course.id, badge=badge1)
        UserBadgeFactory(user=any_other_user, course_id=self.course.id, badge=badge2)

        mock_get_course_badges.return_value = dict()
        response = self.client.get(reverse('my_badges', kwargs={'course_id': self.course.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        mock_get_course_badges.assert_called_once_with(self.user, self.course.id, [user_badge])
