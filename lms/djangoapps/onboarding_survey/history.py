"""
Module to populate history table for the user.
"""
from django.utils import timezone

from lms.djangoapps.onboarding_survey.models import (
    History
)


def add_fields(fields, add_from, add_to, fields_mapping=None):
    """
    Adds fields from one model to another.

    Arguments:
        fields(list): list of fields(columns) which have same name in both models.
        add_from(model): An instance of model from which values are to be added.
        add_to(model): An instance of model in which values are to be added.
        fields_mapping(dict): In case, fields(columns) don't have same names in models, please provide
                              the mappings in the form of a dictionary. Keys should correspond to the
                              column names in the model in which we want to add fields.
    """

    for field in fields:
        setattr(add_to, field, getattr(add_from, field))

    if fields_mapping:
        for history_table_field_name, original_table_field_name in fields_mapping.items():
            setattr(add_to, history_table_field_name, getattr(add_from, original_table_field_name))


def add_user_info_survey(history, user):
    """
    Function to add user info survey in history

    Arguments:
        history(History): History table model
        user(User): Django user model instance
    """
    # The fields to be added in the history table from user info survey
    fields = [
        'dob', 'language', 'country_of_residence', 'city_of_residence', 'is_emp_location_different',
        'country_of_employment', 'city_of_employment', 'level_of_education', 'english_proficiency'
    ]

    user_info_survey = user.user_info_survey
    add_fields(fields, user_info_survey, history)


def add_interests_survey(history, user):
    """
    Function to add interests survey in history

    Arguments:
        history(History): History table model
        user(User): Django user model instance
    """
    interests_survey = user.interest_survey
    history.reason_of_selected_interest = interests_survey.reason_of_selected_interest

    # We have decided to store every option of ManyToMany field as a separate column.
    many_to_many_fields_mapping = {
        # OrgCapacityArea
        'Logistics': 'org_capacity_logistics',
        'Administration': 'org_capacity_administration',
        'Finance': 'org_capacity_finance',
        'External Relations': 'org_capacity_external_relation',
        'Programs': 'org_capacity_program',
        'Leadership': 'org_capacity_leadership',
        # Personal Goal
        'Gain new skills': 'goal_gain_new_skill',
        'Build relationship with other nonprofit practitioners': 'goal_relation_with_other',
        'Develop my leadership abilities': 'goal_develop_leadership',
        'Improve my job prospects': 'goal_improve_job_prospect',
        'Contribute to my organization\'s capacity': 'goal_contribute_to_org',
        # CommunityTypeInterest
        'A community learners working for similar organizations': 'coi_similar_org',
        'A community of learners interested in the same organizational capacity areas': 'coi_similar_org_capacity',
        'A community of learners from my region or country': 'coi_same_region',
    }

    for capacity_area_choice in interests_survey.capacity_areas.all():
        setattr(history, many_to_many_fields_mapping[capacity_area_choice.label], True)

    for personal_goal_choice in interests_survey.personal_goal.all():
        setattr(history, many_to_many_fields_mapping[personal_goal_choice.label], True)

    for interested_communities_choice in interests_survey.interested_communities.all():
        setattr(history, many_to_many_fields_mapping[interested_communities_choice.label], True)


def add_organization_survey(history, user):
    """
    Function to add organization survey in history

    Arguments:
        history(History): History table model
        user(User): Django user model instance
    """

    # The fields to be added in the history table from organization survey
    fields = ['role_in_org', 'partner_network']
    # Some of the fields in history table have different corresponding names in organization survey.
    history_and_org_survey_field_mappings = {
        'org_sector': 'sector',
        'org_level_of_operation': 'level_of_operation',
        'org_focus_area': 'focus_area',
        'org_total_employees': 'total_employees',
        'org_total_volunteers': 'total_volunteers',
        'org_start_month_year': 'start_month_year',
        'org_country': 'country',
        'org_city': 'city',
        'org_url': 'url',
        'org_founding_year': 'founding_year',
        'org_total_clients': 'total_clients',
        'org_total_revenue': 'total_revenue',
    }

    organization_survey = user.organization_survey
    add_fields(fields, organization_survey, history, history_and_org_survey_field_mappings)


def add_extended_registration(history, user):
    """
    Function to add extended profile fields in history

    Arguments:
        history(History): History table model
        user(User): Django user model instance
    """

    # The fields to be added in the history table from extended profile
    fields = ['first_name', 'last_name', 'organization', 'is_poc', 'is_currently_employed', 'org_admin_email']

    extended_profile = user.extended_profile
    add_fields(fields, extended_profile, history)


def populate_history(user):
    """
    populate user history.

    Arguments:
        user(User): Django user model instance

    Returns
        history: Newly created History model instance
    """
    history = History()
    add_user_info_survey(history, user)
    add_interests_survey(history, user)
    add_organization_survey(history, user)
    add_extended_registration(history, user)
    history.user = user
    return history


def save_history(history, user):
    """
    Save user history.

    It will update the previous(if any) entry of history for the same user
    by added value in end_date column. It then, will create a new entry in the
    history table.

    Arguments:
        history(History): History table model
        user(User): Django user model instance
    """
    most_recent_history = History.objects.filter(user=user, end_date=None).first()
    if most_recent_history:
        most_recent_history.end_date = timezone.now()
        most_recent_history.save()
    history.save()


def update_history(user):
    """
    Update user history.Call this function whenever there is need to update the user history.

    Arguments:
        user(User): Django user Model instance
    """
    history = populate_history(user)
    save_history(history, user)
