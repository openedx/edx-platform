from datetime import datetime, timedelta

from django.contrib.auth.models import Permission
from mock import patch
from organizations.tests.factories import UserFactory

from custom_settings.tests.factories import CustomSettingsFactory
from openedx.features.partners import helpers
from openedx.features.partners.tests.factories import (
    CourseCardFactory,
    PartnerCommunityFactory,
    PartnerCourseOverviewFactory,
    PartnerFactory,
    PartnerUserFactory
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class PartnerHelpersTest(ModuleStoreTestCase):
    """ Test cases for openedx partner feature helpers """

    PARTNER_SLUG = 'ignite'
    PARTNER_PERMISSION = 'can_access_{slug}_performance'.format(slug=PARTNER_SLUG)
    ORGANIZATION = 'arbisoft'
    ATTRIBUTE_NAME = 'description'

    def setUp(self):
        super(PartnerHelpersTest, self).setUp()
        self.user = UserFactory()
        self.partner = PartnerFactory.create(slug=self.PARTNER_SLUG, label=self.ORGANIZATION)
        self.partner_user = PartnerUserFactory(user=self.user, partner=self.partner)
        self.course = CourseFactory.create()

    def test_import_form_using_slug_with_invalid_slug(self):
        """
        Test None is returned for an invalid partner slug
        :return : None
        """
        form = helpers.import_form_using_slug('invalid')
        self.assertIsNone(form)

    def test_get_course_description_with_invalid_course(self):
        """
        Verify that empty string is returned for invalid course
        """
        self.assertEqual(helpers.get_course_description(None), '')

    def test_get_partner_recommended_courses_with_valid_partner(self):
        """
        Create Custom settings, Course overview and Course Card
        :return : list of recommended courses
        """
        CustomSettingsFactory(id=self.course.id, tags=self.PARTNER_SLUG)
        PartnerCourseOverviewFactory(id=self.course.id)
        CourseCardFactory(course_id=self.course.id, course_name=self.course.name)

        recommended_courses = helpers.get_partner_recommended_courses(self.PARTNER_SLUG, self.user)

        self.assertNotEqual(len(recommended_courses), 0)

    def test_get_partner_recommended_courses_with_invalid_custom_settings(self):
        """
        Create Custom settings with invalid partner slug
        Create Course overview and and Course Card
        :return : list of recommended courses
        """
        CustomSettingsFactory(id=self.course.id, tags='invalid')
        PartnerCourseOverviewFactory(id=self.course.id)
        CourseCardFactory(course_id=self.course.id, course_name=self.course.name)

        recommended_courses = helpers.get_partner_recommended_courses(self.PARTNER_SLUG, self.user)

        self.assertEqual(len(recommended_courses), 0)

    def test_get_partner_recommended_courses_without_course_card(self):
        """
        Create Custom settings for partner
        Create Course overview
        :return : list of recommended courses
        """
        CustomSettingsFactory(id=self.course.id, tags=self.PARTNER_SLUG)
        PartnerCourseOverviewFactory(id=self.course.id)

        recommended_courses = helpers.get_partner_recommended_courses(self.PARTNER_SLUG, self.user)

        self.assertEqual(len(recommended_courses), 0)

    def test_get_partner_recommended_courses_with_invalid_partner(self):
        """
        Test empty list of recommendation is returned for invalid partner
        :return : list of recommended courses
        """
        recommended_courses = helpers.get_partner_recommended_courses('invalid', self.user)
        self.assertEqual(len(recommended_courses), 0)

    def test_get_partner_recommended_courses_with_invalid_enrollment_start_date(self):
        """
        Test empty list of recommendation is returned if enrolment start date is in the future
        :return : list of recommended courses
        """
        # get a future date
        enrollment_date = datetime.now() + timedelta(days=2)
        PartnerCourseOverviewFactory(id=self.course.id, enrollment_start=enrollment_date)

        recommended_courses = helpers.get_partner_recommended_courses(self.PARTNER_SLUG, self.user)
        self.assertEqual(len(recommended_courses), 0)

    def test_get_partner_recommended_courses_with_invalid_enrollment_end_date(self):
        """
        Test empty list of recommendation is returned if enrolment end is in the past
        :return : list of recommended courses
        """
        # get a future date
        enrollment_date = datetime.now() + timedelta(days=-2)
        PartnerCourseOverviewFactory(id=self.course.id, enrollment_start=enrollment_date)

        recommended_courses = helpers.get_partner_recommended_courses(self.PARTNER_SLUG, self.user)
        self.assertEqual(len(recommended_courses), 0)

    @patch('openedx.features.partners.helpers.log.info')
    def test_auto_join_partner_community_with_valid_partner_community(self, mock_log_info):
        """
        log.info method gets called when task is successfully
        added to celery. Using mock make sure that log.info gets
        called
        Create a partner and partner community
         :return : None
        """
        PartnerCommunityFactory(partner=self.partner)
        helpers.auto_join_partner_community(self.partner, self.user)
        assert mock_log_info.called_once

    @patch('openedx.features.partners.helpers.log.info')
    def test_auto_join_partner_community_with_multiple_partner_community(self, mock_log_info):
        """
        Test that log.info method gets called for all added
        communities for a partner
        Create 2 partner communities
        :return : None
        """
        PartnerCommunityFactory(partner=self.partner)
        PartnerCommunityFactory(partner=self.partner)
        helpers.auto_join_partner_community(self.partner, self.user)
        self.assertEqual(mock_log_info.call_count, 2)

    @patch('openedx.features.partners.helpers.log.info')
    def test_auto_join_partner_community_without_partner_community(self, mock_log_info):
        """
        log.info method gets called when task is successfully
        added to celery. Using mock make sure that log.info gets
        called
        :return : None
        """
        helpers.auto_join_partner_community(self.partner, self.user)
        assert mock_log_info.not_called

    def test_get_partner_from_user_with_partner(self):
        """
        Test that valid partner object is returned against user
        :return: partner
        """
        self.assertEqual(helpers.get_partner_from_user(self.user), self.partner)

    def test_get_partner_from_user_without_partner_user_relation(self):
        """
        Test that none is returned if a bridget between user and partner
        is not created
        @return: partner
        """
        user = UserFactory()
        self.assertIsNone(helpers.get_partner_from_user(user))

    def test_user_has_performance_access_with_permission(self):
        """
        Test that a user with a valid permission has access to performance page
        Give user permission to access performance page
        :return: bool
        """
        permission = Permission.objects.filter(codename=self.PARTNER_PERMISSION).first()
        if permission:
            self.user.user_permissions.add(permission)
        self.assertTrue(helpers.user_has_performance_access(self.user, self.partner))

    def test_user_has_performance_access_without_permission(self):
        """
        Test user is unable to access performance page without a valid permission
        Create a new user without permission
        :return: bool
        """
        self.assertFalse(helpers.user_has_performance_access(self.user, self.partner))
