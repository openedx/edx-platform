# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def are_surveys_complete(apps, user):
    """
    Checks whether surveys are complete or not.

    There are three surveys, user info, interests and organization survey.
    This function returns true iff user has entries for all these surveys.

    Arguments:
        apps(Apps): A registry that stores the configuration of installed applications.
        user(User): The user for which we want to check surveys

    Returns:
        boolean: True iff all surveys are complete.
    """
    usr_info_survey_model = apps.get_model("onboarding_survey", "UserInfoSurvey")
    interests_survey_model = apps.get_model("onboarding_survey", "InterestsSurvey")
    org_survey_model = apps.get_model("onboarding_survey", "OrganizationSurvey")
    surveys_are_complete = True
    try:
        user.user_info_survey
        user.interest_survey
        user.organization_survey
    except (usr_info_survey_model.DoesNotExist, interests_survey_model.DoesNotExist, org_survey_model.DoesNotExist):
        surveys_are_complete = False

    return surveys_are_complete


def get_first_and_last_name(name):
    """
    Splits name on space and returns the values

    In case there are more than one spaces, we ignore all values
    except the first and last. If there is no space, then, both,
    first name and last name, would be equal to name.

    Arguments:
        name(str): The full name.

    Returns:
        list: A list containing first name and last name(in the same order).
    """
    name_splits = name.split(' ')
    if len(name_splits) == 2:
        return name_splits
    elif len(name_splits) > 2:
        return [name_splits[0], name_splits[-1]]
    else:
        return name_splits * 2


def get_name(apps, user):
    """
    Get the name of the user

    If user doesn't have profile attribute or profile has empty name then
    we use user's unique public username otherwise 'name' from user's profile.

    Arguments:
        apps(Apps): A registry that stores the configuration of installed applications.
        user(User): The user of which to get the name

    Returns:
        str: The name of the user.
    """
    user_profile_model = apps.get_model("student", "UserProfile")
    try:
        name = user.profile.name
        if not name:
            return user.username
        return name
    except user_profile_model.DoesNotExist:
        return user.username


def create_extended_profile(apps, user):
    """
    Create extended profile for user

    Arguments:
        apps(Apps): A registry that stores the configuration of installed applications.
        user(User): The user for which we want to create extended profile.
    """
    extended_profile_model = apps.get_model("onboarding_survey", "ExtendedProfile")
    organization_model = apps.get_model("onboarding_survey", "Organization")

    extended_profile = extended_profile_model()
    first_name, last_name = get_first_and_last_name(get_name(apps, user))

    extended_profile.user = user
    extended_profile.first_name = first_name
    extended_profile.last_name = last_name
    organization, created = organization_model.objects.get_or_create(name='PhilU')
    extended_profile.organization = organization
    extended_profile.org_admin_email = ''
    extended_profile.is_survey_completed = are_surveys_complete(apps, user)

    extended_profile.save()


def create_user_profile(apps, user):
    """
    Create edX's user profile for the user.

    Many features in the edX depend upon some of the fields in this model.

    Arguments:
        apps(Apps): A registry that stores the configuration of installed applications.
        user(User): Django auth user model instance corresponding
                    the user of which to create the user profile.
    """
    user_profile_model = apps.get_model("student", "UserProfile")
    user_profile = user_profile_model()
    user_profile.name = user.username
    user_profile.user = user
    user_profile.save()


class Migration(migrations.Migration):

    def fix_broken_profiles(apps, schema_editor):

        extended_profile_model = apps.get_model("onboarding_survey", "ExtendedProfile")
        user_profile_model = apps.get_model("student", "UserProfile")
        user_model = apps.get_model("auth", "User")

        users = user_model.objects.exclude(username__in=['honor', 'ecommerce_worker', 'verified', 'audit', 'user'])

        for user in users:
            try:
                user.extended_profile
            except extended_profile_model.DoesNotExist:
                create_extended_profile(apps, user)

            try:
                user.profile
            except user_profile_model.DoesNotExist:
                create_user_profile(apps, user)

    dependencies = [
        ('onboarding_survey', '0030_auto_20171002_1110'),
        ('student', '0014_auto_20170914_0817')
        ]

    operations = [
        migrations.RunPython(fix_broken_profiles),
        ]
