""" Serializers for teams application """
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturaltime
from rest_framework import serializers

from lms.djangoapps.teams.serializers import (
    CountryField,
    CourseTeamCreationSerializer,
    CourseTeamSerializer,
    UserMembershipSerializer
)

from .helpers import generate_random_team_banner_color, generate_random_user_icon_color


class CustomCountryField(CountryField):
    """ Field to serialize country code """

    def to_internal_value(self, data):
        """ Check that the code is a valid country code.

        We leave the data in its original format so that the Django model's
        CountryField can convert it to the internal representation used
        by the django-countries library.
        :param dict data: Country code
        :return: Valid country code
        :rtype: dict
        """

        if not data:
            raise serializers.ValidationError(
                "Country field is required"
            )

        if data and data not in self.COUNTRY_CODES:
            raise serializers.ValidationError(
                u"{code} is not a valid country code".format(code=data)
            )
        return data


class CustomLanguageField(serializers.Field):
    """ Field to serialize a Language code. """

    LANGUAGE_CODES = dict(settings.ALL_LANGUAGES).keys()

    def to_representation(self, value):
        """ Represent the country as a 2-character unicode identifier.
        :param (char) value: Field value
        :return: Unicode representation of value
        :rtype: unicode
        """
        return unicode(value)

    def to_internal_value(self, data):
        """ Check that the code is a valid language code.

        We leave the data in its original format so that the Django model's
        CountryField can convert it to the internal representation used
        by the django-countries library.
        :param dict data: Language code
        :return: Valid language code
        :rtype: dict
        """

        if not data:
            raise serializers.ValidationError(
                "Language field is required"
            )

        if data and data not in self.LANGUAGE_CODES:
            raise serializers.ValidationError(
                u"{code} is not a valid language code".format(code=data)
            )
        return data


class CustomCourseTeamCreationSerializer(CourseTeamCreationSerializer):
    """ Custom serializer for course team creation """
    country = CustomCountryField(required=True)
    language = CustomLanguageField(required=True)


class CustomUserMembershipSerializer(UserMembershipSerializer):
    """ Custom serializer for user membership inherittes from CourseTeamMembership"""
    class Meta(object):
        model = UserMembershipSerializer.Meta.model
        fields = UserMembershipSerializer.Meta.fields + (
            'profile_color', 'last_activity_natural', 'date_joined_natural'
        )
        read_only_fields = UserMembershipSerializer.Meta.read_only_fields

    profile_color = serializers.SerializerMethodField()
    last_activity_natural = serializers.SerializerMethodField()
    date_joined_natural = serializers.SerializerMethodField()

    def get_profile_color(self, membership):  # pylint: disable=unused-argument
        """ Get profile color
        :param CourseTeamMembership membership: Course team membership model object
        :return: Hex color code , i.e #FFFFFF
        :rtype: string
        """
        return generate_random_user_icon_color()

    def get_last_activity_natural(self, membership):
        """ Get last activity time in human readable format i.e. a minute ago, 2 hours ago etc
        :param CourseTeamMembership membership: Course team membership model object
        :return: Natural date time
        :rtype: string
        """
        return naturaltime(membership.last_activity_at)

    def get_date_joined_natural(self, membership):
        """ Get joined date time in human readable format i.e. a minute ago, 2 hours ago etc
        :param CourseTeamMembership membership: Course team membership model object
        :return: Natural date time
        :rtype: string
        """
        return naturaltime(membership.date_joined)


class CustomCourseTeamSerializer(CourseTeamSerializer):
    """ Custom serializer for course team """
    country = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    banner_color = serializers.SerializerMethodField()
    membership = CustomUserMembershipSerializer(many=True, read_only=True)

    class Meta(object):
        model = CourseTeamSerializer.Meta.model
        fields = CourseTeamSerializer.Meta.fields + ('banner_color', 'team_id')
        read_only_fields = CourseTeamSerializer.Meta.read_only_fields

    def get_country(self, course_team):
        """ Get course team banner country
        :param CourseTeam course_team: Course team model object
        :return: Country name
        :rtype: string
        """
        return course_team.country.name.format()

    def get_language(self, course_team):
        """ Get valid corresponding language from settings otherwise return course team language
        :param CourseTeam course_team: Course team model object
        :return: Course team language
        :rtype: list
        """
        languages = dict(settings.ALL_LANGUAGES)
        try:
            return languages[course_team.language]
        except KeyError:
            return course_team.language

    def get_banner_color(self, course_team):  # pylint: disable=unused-argument
        """ Get course team banner color
        :param CourseTeam course_team: Course team model object
        :return: Hex color code , i.e #FFFFFF
        :rtype: string
        """
        return generate_random_team_banner_color()
