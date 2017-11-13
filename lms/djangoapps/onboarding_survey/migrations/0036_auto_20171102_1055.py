# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

edu_levels = ["Doctoral or professional degree", "Master's degree", "Bachelor's degree",
              "Some university, no degree", "High school diploma or equivalent secondary degree",
              "No formal educational degree", "I'd rather not say"]

en_profs = ["No proficiency", "Beginning", "Intermediate", "Advanced", "Native speaker",
            "I'd rather not say"]

roles_in_org = ["Volunteer", "Internship", "Entry level", "Manager",
                "Director", "Executive", "I'd rather not say"]

func_areas = ["Strategy and planning", "Leadership and governance", "Program design and development",
              "Measurement, evaluation, and learning", "Stakeholder engagement and partnerships",
              "Human resource management", "Financial management" , "Fundraising and resource mobilization",
              "Marketing, communications, and PR", "Systems, tools, and processes"]

org_capacity = func_areas

community_interests = ["Learners from my region or country",
                       "Learners interested in the same areas of organizational effectiveness",
                       "Learners working for similar organizations", "Learners who are different from me"]

personal_goals = ["Help improve my organization", "Develop new skills", "Get a new job",
                  "Build relationships with other nonprofit leaders"]

org_sector = ["Academic Institution", "For-Profit Company", "Government Agency",
              "Grantmaking Foundation", "Non-Profit Organization", "Self-Employed",
              "Social Enterprise", "I'd rather not say"]

operation_levels = ["International", "Regional including offices in multiple countries", "National",
                    "Regional including multiple offices within one country", "Local", "I'd rather not say"]

focus_areas = ["Animals", "Arts, Culture, Humanities","Community Development", "Education", "Environment",
               "Health", "Human and Civil Rights", "Human Services", "International", "Religion",
               "Research and Public Policy", "I'd rather not say"]

total_employees = ["1 (only yourself)", "2-5", "6-10", "11-20", "21-50", "51-100", "101-200", "201-501",
                   "501-1,000", "1,000+", "Not applicable"]

partner_network = ["+Acumen", "FHI 360 / FHI Foundation", "Global Giving", "Mercy Corps"]


def populate_partner_network(apps, model, updated_list):
    _model = apps.get_model("onboarding_survey", model)
    _model.objects.all().delete()

    for name in updated_list:
        obj = _model(name=name.encode('utf8'))
        obj.save()


def populate_model(apps, model, updated_list):
    _model = apps.get_model("onboarding_survey", model)
    _model.objects.all().delete()

    for label in updated_list:
        obj = _model(label=label.encode('utf8'))
        obj.save()


def update_org_survey(apps):
    org_survey_model = apps.get_model("onboarding_survey", "OrganizationSurvey")
    sector_model = apps.get_model("onboarding_survey", "OrgSector")
    operation_level_model = apps.get_model("onboarding_survey", "OperationLevel")
    focus_area_model = apps.get_model("onboarding_survey", "FocusArea")
    total_employee_model = apps.get_model("onboarding_survey", "TotalEmployee")
    partner_network_model = apps.get_model("onboarding_survey", "PartnerNetwork")

    org_surveys = org_survey_model.objects.all()

    sector = sector_model.objects.first()
    operation_level = operation_level_model.objects.first()
    focus_area = focus_area_model.objects.first()
    total_employee = total_employee_model.objects.first()

    for org_survey in org_surveys:
        org_survey.sector = sector
        org_survey.level_of_operation = operation_level
        org_survey.focus_area = focus_area
        org_survey.total_employees = total_employee
        org_survey.partner_network.add(partner_network_model.objects.first())
        org_survey.save()


def update_interest_survey(apps):
    interest_survey_model = apps.get_model("onboarding_survey", "InterestsSurvey")
    capacity_area_model = apps.get_model("onboarding_survey", "OrganizationalCapacityArea")
    community_interests_model = apps.get_model("onboarding_survey", "CommunityTypeInterest")
    personal_goal_model = apps.get_model("onboarding_survey", "PersonalGoal")

    interest_surveys = interest_survey_model.objects.all()

    capacity_area = capacity_area_model.objects.first()
    community_interest = community_interests_model.objects.first()
    personal_goal = personal_goal_model.objects.first()

    for interest_survey in interest_surveys:
        interest_survey.capacity_areas.add(capacity_area)
        interest_survey.interested_communities.add(community_interest)
        interest_survey.personal_goal.add(personal_goal)
        interest_survey.save()


def update_userinfo_survey(apps):
    userinfo_survey_model = apps.get_model("onboarding_survey", "UserInfoSurvey")
    edu_level_model = apps.get_model("onboarding_survey", "EducationLevel")
    en_prof_model = apps.get_model("onboarding_survey", "EnglishProficiency")
    org_role_model = apps.get_model("onboarding_survey", "RoleInsideOrg")
    func_area_model = apps.get_model("onboarding_survey", "FunctionArea")

    user_info_surveys = userinfo_survey_model.objects.all()

    edu_level = edu_level_model.objects.first()
    en_prof = en_prof_model.objects.first()
    org_role = org_role_model.objects.first()
    func_area = func_area_model.objects.first()

    for user_info_survey in user_info_surveys:
        user_info_survey.level_of_education = edu_level
        user_info_survey.english_proficiency = en_prof
        user_info_survey.role_in_org = org_role
        user_info_survey.function_area.add(func_area)
        user_info_survey.save()


class Migration(migrations.Migration):

    def populate_required_tables(apps, schema_editor):

        model_list = ["EducationLevel", "EnglishProficiency", "RoleInsideOrg", "FunctionArea", "OrganizationalCapacityArea",
                      "CommunityTypeInterest", "PersonalGoal", "OrgSector", "OperationLevel", "FocusArea", "TotalEmployee"]

        list_of_updated_lists = [edu_levels, en_profs, roles_in_org, func_areas, org_capacity, community_interests,
                                 personal_goals, org_sector, operation_levels, focus_areas, total_employees]

        for i in range(0,len(model_list)):
            populate_model(apps, model_list[i], list_of_updated_lists[i])

        populate_partner_network(apps, "PartnerNetwork", partner_network)

        update_org_survey(apps)
        update_interest_survey(apps)
        update_userinfo_survey(apps)

    dependencies = [
        ('onboarding_survey', '0035_auto_20171101_0708'),
    ]

    operations = [
        migrations.RunPython(populate_required_tables),
    ]
