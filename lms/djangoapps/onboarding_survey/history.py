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
        'year_of_birth', 'language', 'country_of_residence', 'city_of_residence', 'is_emp_location_different',
        'country_of_employment', 'city_of_employment', 'start_month_year', 'weekly_work_hours' 'level_of_education',
        'english_proficiency', 'role_in_org'
    ]

    many_many_fields_mapping = {
        'Strategy and planning': 'user_fn_strategy_and_planning',
        'Leadership and governance': 'user_fn_leadership_and_gov',
        'Program design and development': 'user_fn_program_design_and_dev',
        'Measurement, evaluation, and learning': 'user_fn_measurement_and_learning',
        'Stakeholder engagement and partnerships': 'user_fn_engagement_and_partnership',
        'Human resource management': 'user_fn_human_resource',
        'Financial management': 'user_fn_financial_management',
        'Fundraising and resource mobilization': 'user_fn_fundraising_and_mobilization',
        'Marketing, communications, and PR': 'user_fn_marketing_and_PR',
        'Systems, tools, and processes': 'user_fn_system_and_process',
    }

    user_info_survey = user.user_info_survey
    add_fields(fields, user_info_survey, history)

    for function_area in user_info_survey.function_area.all():
        setattr(history, many_many_fields_mapping[function_area.label], True)


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
        # New values(Org Effectiveness)
        'Strategy and planning': 'org_eff_strategy_and_planning',
        'Leadership and governance': 'org_eff_leadership_and_gov',
        'Program design and development': 'org_eff_program_design_and_dev',
        'Measurement, evaluation, and learning': 'org_eff_measurement_and_learning',
        'Stakeholder engagement and partnerships': 'org_eff_engagement_and_partnership',
        'Human resource management': 'org_eff_human_resource',
        'Financial management': 'org_eff_financial_management',
        'Fundraising and resource mobilization': 'org_eff_fundraising_and_mobilization',
        'Marketing, communications, and PR': 'org_eff_marketing_and_PR',
        'Systems, tools, and processes': 'org_eff_system_and_process',
        # Personal Goal
        'Gain new skills': 'goal_gain_new_skill',
        'Build relationship with other nonprofit practitioners': 'goal_relation_with_other',
        'Develop my leadership abilities': 'goal_develop_leadership',
        'Improve my job prospects': 'goal_improve_job_prospect',
        'Contribute to my organization\'s capacity': 'goal_contribute_to_org',
        # CommunityTypeInterest
        'Learners working for similar organizations': 'coi_similar_org',
        'Learners interested in the same areas of organizational effectiveness': 'coi_similar_org_capacity',
        'Learners from my region or country': 'coi_same_region',
        'Learners who are different from me': 'coi_diff_from_me'
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

    # Partner Network
    many_to_many_fields_mapping = {
        'Mercy Corps': 'partner_network_mercy_corps',
        'Global Giving': 'partner_network_global_giving',
        'FHI 360 / FHI Foundation': 'partner_network_fhi_360',
        '+Acumen': 'partner_network_acumen',
    }
    # Some of the fields in history table have different corresponding names in organization survey.
    history_and_org_survey_field_mappings = {
        'org_sector': 'sector',
        'org_level_of_operation': 'level_of_operation',
        'org_focus_area': 'focus_area',
        'org_total_employees': 'total_employees',
        'org_country': 'country',
        'org_city': 'city',
        'org_is_url_exist': 'is_org_url_exist',
        'org_url': 'url',
        'org_founding_year': 'founding_year',
        'org_alternate_admin_email': 'alternate_admin_email'
    }

    organization_survey = user.organization_survey
    add_fields(None, organization_survey, history, history_and_org_survey_field_mappings)

    for partner_network in organization_survey.partner_network.all():
        setattr(history, many_to_many_fields_mapping[partner_network.name], True)


def add_organization_detail_survey(history, user):

    fields = [
        'info_accuracy', 'can_provide_info', 'last_fiscal_year_end_date', 'currency',
        'total_clients', 'total_employees', 'total_revenue', 'total_expenses', 'total_program_expenses'
    ]
    org_detail_survey = user.org_detail_survey

    add_fields(fields, org_detail_survey, history)


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
    add_organization_detail_survey(history, user)
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
