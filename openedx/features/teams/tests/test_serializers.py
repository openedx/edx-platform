""" Test class for teams serializer """
import factory
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import signals
from django.test.client import RequestFactory

from lms.djangoapps.onboarding.tests.factories import UserFactory
from lms.djangoapps.teams.tests.factories import CourseTeamFactory, CourseTeamMembershipFactory
from openedx.features.teams.helpers import TEAM_BANNER_COLORS, USER_ICON_COLORS
from openedx.features.teams.serializers import (
    CustomCourseTeamCreationSerializer,
    CustomCourseTeamSerializer,
    CustomUserMembershipSerializer
)
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

VALID_COUNTRY = 'LA'
VALID_LANGUAGE = 'kl'
INVALID_COUNTRY = 'Test Country'
INVALID_LANGUAGE = 'Test Language'

REQUIRED_ERROR_MSG = {'COUNTRY': ['Country field is required'], 'LANGUAGE': ['Language field is required']}
INVALID_COUNTRY_CODE = '{country_code} is not a valid country code'
INVALID_LANGUAGE_CODE = '{language_code} is not a valid language code'


class SerializersTestBaseClass(ModuleStoreTestCase):
    """ Base class for common steps required for testing serializers """

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        """ create required data for testing serializers in the module """
        super(SerializersTestBaseClass, self).setUp()
        org = 'edX'
        course_number = 'CS101'
        course_run = '2015_Q1'
        display_name = 'test course 1'

        course = CourseFactory.create(
            org=org,
            number=course_number,
            run=course_run,
            display_name=display_name,
            default_store=ModuleStoreEnum.Type.split,
            teams_configuration={
                "max_team_size": 10,
                "topics": [{u'name': u'T0pic', u'description': u'The best topic!', u'id': u'0'}]
            }
        )
        course.save()
        self.team = CourseTeamFactory.create(
            course_id=course.id,
            topic_id=course.teams_topics[0]['id'],
            name='Test Team',
            description='Testing Testing Testing...',
        )


class CreateTeamsSerializerTestCase(SerializersTestBaseClass):
    """ Tests for the create team serializer."""

    def _get_team_dict_data(self):
        data = self.team.__dict__
        data['course_id'] = data['course_id'].to_deprecated_string()
        return data

    def test_case_create_team__with_empty_language_field(self):
        """ Test that correct error message is thrown when serializing team with empty language field"""
        self.team.country = VALID_COUNTRY
        data = self._get_team_dict_data()
        expected_result = {'language': REQUIRED_ERROR_MSG['LANGUAGE']}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_create_team_with_invalid_language_code(self):
        """ Test that correct error message is thrown when serializing team with invalid language value"""
        self.team.country = VALID_COUNTRY
        self.team.language = INVALID_LANGUAGE
        data = self._get_team_dict_data()
        expected_result = {'language': [INVALID_LANGUAGE_CODE.format(language_code=self.team.language)]}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_create_team_with_empty_country_field(self):
        """ Test that correct error message is thrown when serializing team with empty country field"""
        self.team.language = VALID_LANGUAGE
        data = self._get_team_dict_data()
        expected_result = {'country': REQUIRED_ERROR_MSG['COUNTRY']}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_create_team_with_invalid_country_code(self):
        """ Test that correct error message is thrown when serializing team with invalid country value"""
        self.team.country = INVALID_COUNTRY
        self.team.language = VALID_LANGUAGE
        data = self._get_team_dict_data()
        expected_result = {'country': [INVALID_COUNTRY_CODE.format(country_code=self.team.country)]}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_create_team_with_empty_language_and_country_fields(self):
        """ Test that correct error message is thrown when serializing team with both empty language field
        and empty country field
        """
        data = self._get_team_dict_data()
        expected_result = {'country': REQUIRED_ERROR_MSG['COUNTRY'], 'language': REQUIRED_ERROR_MSG['LANGUAGE']}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_create_team_with_invalid_language_and_country_fields(self):
        """ Test that correct error message is thrown when serializing team with both invalid language field
        and invalid country field
        """
        self.team.country = INVALID_COUNTRY
        self.team.language = INVALID_LANGUAGE
        data = self._get_team_dict_data()
        expected_result = {'country': [INVALID_COUNTRY_CODE.format(country_code=self.team.country)],
                           'language': [INVALID_LANGUAGE_CODE.format(language_code=self.team.language)]}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_create_team_with_valid_language_and_country_fields(self):
        """ Test that no errors are returned when team has valid language and country values """
        self.team.country = VALID_COUNTRY
        self.team.language = VALID_LANGUAGE
        data = self._get_team_dict_data()
        expected_result = {}
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.errors, expected_result)

    def test_case_valid_language_representation(self):
        """ Test that after serializing team object language is represented correctly in unicode"""
        self.team.country = VALID_COUNTRY
        self.team.language = VALID_LANGUAGE
        data = self._get_team_dict_data()
        valid_result = unicode(self.team.language)
        serialized_data = CustomCourseTeamCreationSerializer(data=data)
        serialized_data.is_valid()
        self.assertEqual(serialized_data.data['language'], valid_result)


class CustomUserMembershipSerializerTestCase(SerializersTestBaseClass):
    """ Test cases for CustomUserMembershipSerializer """

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        """ Create required data for testing CustomUserMembershipSerializer.
        create a new user and join that user in the testing team.
        """
        super(CustomUserMembershipSerializerTestCase, self).setUp()
        self.user = UserFactory.create()
        self.membership = CourseTeamMembershipFactory.create(team=self.team, user=self.user)

    def test_case_validate_profile_color(self):
        """ Test that correct color is stored in serialized data"""
        data = CustomUserMembershipSerializer(self.membership, context={
            'expand': [u'team', u'user'],
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        self.assertIn(data['profile_color'], USER_ICON_COLORS)

    def test_case_validate_natural_last_activity(self):
        """ Test that last_activity is stored in valid natural format after serializing the data"""
        data = CustomUserMembershipSerializer(self.membership, context={
            'expand': [u'team', u'user'],
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        self.assertEqual(data['last_activity_natural'], naturaltime(self.membership.last_activity_at))

    def test_case_validate_natural_date_joined(self):
        """ Test that date_joined is stored in valid natural format after serializing the data"""
        data = CustomUserMembershipSerializer(self.membership, context={
            'expand': [u'team', u'user'],
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        self.assertEqual(data['date_joined_natural'], naturaltime(self.membership.date_joined))


class CustomCourseTeamSerializerTestCase(SerializersTestBaseClass):
    """ Test cases for CustomCourseTeamSerializer """

    def test_case_validate_team_country(self):
        """ Test that formatted(full) country name is stored in serialized data"""
        self.team.country = VALID_COUNTRY
        data = CustomCourseTeamSerializer(self.team, context={
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        self.assertEqual(data['country'], self.team.country.name.format())

    def test_case_validate_team_language(self):
        """ Test that formatted(full) language name is stored in serialized data"""
        self.team.language = VALID_LANGUAGE
        data = CustomCourseTeamSerializer(self.team, context={
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        languages = dict(settings.ALL_LANGUAGES)
        self.assertEqual(data['language'], languages[self.team.language])

    def test_case_team_with_invalid_language(self):
        """ Test that language name is stored as it is if the given language code does not exist in valid
        languages list
        """
        self.team.language = INVALID_LANGUAGE
        data = CustomCourseTeamSerializer(self.team, context={
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        self.assertEqual(data['language'], self.team.language)

    def test_case_validate_team_banner_color(self):
        """ Test that valid team banner color is stored in serialized data """
        data = CustomCourseTeamSerializer(self.team, context={
            'request': RequestFactory().get('/api/team/v0/team_membership')
        }).data
        self.assertIn(data['banner_color'], TEAM_BANNER_COLORS)
