"""
Models to support the on-boarding surveys
"""
import logging
from datetime import datetime
import re

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django.db import models

log = logging.getLogger("edx.onboarding_survey")


class Organization(models.Model):
    """
    Represents an organization.
    """

    name = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    admin = models.ForeignKey(
        User, related_name='organization', blank=True, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name


class ExtendedProfile(models.Model):
    """
    Model for extra fields in registration form.
    """
    POC_CHOICES = ((0, 'No'), (1, 'Yes'))

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        Organization, related_name='extended_profiles', blank=True, null=True, on_delete=models.SET_NULL
    )
    is_poc = models.BooleanField(choices=POC_CHOICES, default=False)
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='extended_profile')
    org_admin_email = models.EmailField(blank=True, null=True)
    is_survey_completed = models.BooleanField(default=False)
    backup_user_data = models.TextField()


class RoleInsideOrg(models.Model):
    """
    Specifies what is the role of a user inside the organization.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class OrgSector(models.Model):
    """
    Specifies what sector the organization is working in.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class OperationLevel(models.Model):
    """
    Specifies the level of organization like national, international etc.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class FocusArea(models.Model):
    """
    The are of focus of an organization.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class TotalEmployee(models.Model):
    """
    Total employees in an organization.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class TotalVolunteer(models.Model):
    """
    Total volunteers in an organization.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class PartnerNetwork(models.Model):
    """
    Specifies about the partner network being used in an organization.
    """
    name = models.CharField(max_length=255)

    is_partner_affiliated = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class SchemaOrNoSchemaURLValidator(URLValidator):
    regex = re.compile(
        r'((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]'
        r'+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w-]*)'
        r'?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)',
        re.IGNORECASE
    )


class OrganizationSurvey(models.Model):
    """
    The model to save the organization survey as provided by the user.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='organization_survey', null=True,
                                blank=True)

    country = models.CharField(max_length=255)
    city = models.CharField(max_length=255, blank=True)
    ORG_URL_EXISTENCE_CHOICES = ((1, 'Yes'), (0, 'No'))

    is_org_url_exist = models.BooleanField(choices=ORG_URL_EXISTENCE_CHOICES, default=True)
    url = models.URLField(max_length=255, blank=True, validators=[SchemaOrNoSchemaURLValidator])

    sector = models.ForeignKey(OrgSector, on_delete=models.CASCADE, related_name='org_survey')
    level_of_operation = models.ForeignKey(OperationLevel, on_delete=models.CASCADE, related_name='org_survey')
    focus_area = models.ForeignKey(FocusArea, on_delete=models.CASCADE, related_name='org_survey')

    founding_year = models.PositiveSmallIntegerField(blank=True, null=True)
    total_employees = models.ForeignKey(
        TotalEmployee, on_delete=models.CASCADE, related_name='org_survey', null=True
    )

    partner_network = models.ManyToManyField(
        PartnerNetwork
    )
    alternate_admin_email = models.EmailField(blank=True, null=True)


class Currency(models.Model):
    name = models.CharField(max_length=255)
    alphabetic_code = models.CharField(max_length=255)


class OrganizationDetailSurvey(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='org_detail_survey', null=True,
                                blank=True)

    CAN_PROVIDE_INFO_CHOICES = ((1, 'Yes'), (0, 'No'))
    INFO_ACCURACY_CHOICES = (
        (1, "Actual - My answers come directly from my organization's official documentation"),
        (0, "Estimated - My answers are my best guesses based on my knowledge of the organization")
    )
    can_provide_info = models.BooleanField(choices=CAN_PROVIDE_INFO_CHOICES, default=True)
    info_accuracy = models.NullBooleanField(choices=INFO_ACCURACY_CHOICES, blank=True, null=True)

    currency = models.ForeignKey(
        Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name='org_detail_survey'
    )

    last_fiscal_year_end_date = models.DateField(blank=True, null=True)

    total_clients = models.PositiveIntegerField(blank=True, null=True)
    total_employees = models.PositiveIntegerField(blank=True, null=True)
    total_revenue = models.BigIntegerField(blank=True, null=True)
    total_expenses = models.BigIntegerField(blank=True, null=True)
    total_program_expenses = models.BigIntegerField(blank=True, null=True)


class OrganizationalCapacityArea(models.Model):
    """
    Capacity are an Organization. This will be used in Interests survey.
    """

    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class CommunityTypeInterest(models.Model):
    """
    The model to used to get info from user about the type of community he/she
    would like to be added. E.g. community according to region, country etc.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class PersonalGoal(models.Model):
    """
    Models user's goal behind joining the platform.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class InterestsSurvey(models.Model):
    """
    The model to store the interests survey as provided by the user.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='interest_survey', null=True, blank=True)
    capacity_areas = models.ManyToManyField(OrganizationalCapacityArea, blank=True)
    interested_communities = models.ManyToManyField(CommunityTypeInterest, blank=True)
    personal_goal = models.ManyToManyField(PersonalGoal, blank=True)


class EducationLevel(models.Model):
    """
    Models education level of the user
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class EnglishProficiency(models.Model):
    """
    Models english proficiency level of the user.
    """
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label


class FunctionArea(models.Model):
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label


class UserInfoSurvey(models.Model):
    """
    The survey to store the basic information about the user.
    """

    year_of_birth = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1900, message='Ensure year of birth is greater than or equal to 1900'),
            MaxValueValidator(
                datetime.now().year, message='Ensure year of birth is less than or equal to {}'.format(
                    datetime.now().year
                )
            )
        ]
    )

    user = models.OneToOneField(
        User, unique=True, db_index=True, related_name='user_info_survey', null=True, blank=True
    )

    level_of_education = models.ForeignKey(
        EducationLevel, on_delete=models.CASCADE, related_name='user_info_survey', null=True
    )

    language = models.CharField(max_length=255)

    english_proficiency = models.ForeignKey(EnglishProficiency, on_delete=models.CASCADE,
                                            related_name='user_info_survey')

    country_of_residence = models.CharField(max_length=255)
    city_of_residence = models.CharField(max_length=255, blank=True)

    is_emp_location_different = models.BooleanField(default=False)

    country_of_employment = models.CharField(max_length=255, blank=True)
    city_of_employment = models.CharField(max_length=255, blank=True)

    role_in_org = models.ForeignKey(
        RoleInsideOrg, on_delete=models.CASCADE, related_name='user_info_survey', null=True
    )
    start_month_year = models.CharField(max_length=100)

    weekly_work_hours = models.PositiveIntegerField(
        validators=[MaxValueValidator(168)]
    )

    function_area = models.ManyToManyField(FunctionArea, blank=True, null=True)


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True)
    # CommunityTypeInterest
    coi_similar_org = models.BooleanField(blank=True, default=False)
    coi_similar_org_capacity = models.BooleanField(blank=True, default=False)
    coi_same_region = models.BooleanField(blank=True, default=False)
    coi_diff_from_me = models.BooleanField(blank=True, default=False)
    # EducationLevel
    level_of_education = models.ForeignKey(
        EducationLevel, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )
    # EnglishProficiency
    english_proficiency = models.ForeignKey(
        EnglishProficiency, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )
    # FocusAreas
    org_focus_area = models.ForeignKey(
        FocusArea, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )
    # OperationLevel
    org_level_of_operation = models.ForeignKey(
        OperationLevel, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )
    # OrgSector
    org_sector = models.ForeignKey(
        OrgSector, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )

    currency = models.ForeignKey(
        Currency, on_delete=models.SET_NULL, blank=True, null=True, related_name='user_history'
    )

    # UserFunctionOrDepartment
    user_fn_strategy_and_planning = models.BooleanField(blank=True, default=False)
    user_fn_leadership_and_gov = models.BooleanField(blank=True, default=False)
    user_fn_program_design_and_dev = models.BooleanField(blank=True, default=False)
    user_fn_measurement_and_learning = models.BooleanField(blank=True, default=False)
    user_fn_engagement_and_partnership = models.BooleanField(blank=True, default=False)
    user_fn_human_resource = models.BooleanField(blank=True, default=False)
    user_fn_financial_management = models.BooleanField(blank=True, default=False)
    user_fn_fundraising_and_mobilization = models.BooleanField(blank=True, default=False)
    user_fn_marketing_and_PR = models.BooleanField(blank=True, default=False)
    user_fn_system_and_process = models.BooleanField(blank=True, default=False)

    # OrgEffectiveness
    org_eff_strategy_and_planning = models.BooleanField(blank=True, default=False)
    org_eff_leadership_and_gov = models.BooleanField(blank=True, default=False)
    org_eff_program_design_and_dev = models.BooleanField(blank=True, default=False)
    org_eff_measurement_and_learning = models.BooleanField(blank=True, default=False)
    org_eff_engagement_and_partnership = models.BooleanField(blank=True, default=False)
    org_eff_human_resource = models.BooleanField(blank=True, default=False)
    org_eff_financial_management = models.BooleanField(blank=True, default=False)
    org_eff_fundraising_and_mobilization = models.BooleanField(blank=True, default=False)
    org_eff_marketing_and_PR = models.BooleanField(blank=True, default=False)
    org_eff_system_and_process = models.BooleanField(blank=True, default=False)

    # PartnerNetwork
    partner_network_mercy_corps = models.BooleanField(blank=True, default=False)
    partner_network_global_giving = models.BooleanField(blank=True, default=False)
    partner_network_fhi_360 = models.BooleanField(blank=True, default=False)
    partner_network_acumen = models.BooleanField(blank=True, default=False)

    # PersonalGoal
    goal_gain_new_skill = models.BooleanField(blank=True, default=False)
    goal_relation_with_other = models.BooleanField(blank=True, default=False)
    goal_improve_job_prospect = models.BooleanField(blank=True, default=False)
    goal_contribute_to_org = models.BooleanField(blank=True, default=False)

    # RoleInsideOrg
    role_in_org = models.ForeignKey(
        RoleInsideOrg, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )

    # TotalEmployees
    org_total_employees = models.ForeignKey(
        TotalEmployee, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )

    # UserInfoSurvey
    language = models.CharField(max_length=255)
    country_of_residence = models.CharField(max_length=255)
    city_of_residence = models.CharField(max_length=255, blank=True)
    is_emp_location_different = models.BooleanField(default=False)
    country_of_employment = models.CharField(max_length=255, blank=True)
    city_of_employment = models.CharField(max_length=255, blank=True)
    year_of_birth = models.PositiveIntegerField(blank=True)
    start_month_year = models.CharField(max_length=100, blank=True, null=True)
    weekly_work_hours = models.PositiveIntegerField(blank=True)

    # OrganizationSurvey
    org_country = models.CharField(max_length=255)
    org_city = models.CharField(max_length=255, blank=True)
    org_is_url_exist = models.BooleanField(default=True)
    org_url = models.URLField(max_length=255, blank=True)
    org_founding_year = models.PositiveSmallIntegerField(blank=True, null=True)
    org_alternate_admin_email = models.EmailField(blank=True, null=True)

    # OrganizationDetail
    info_accuracy = models.NullBooleanField(blank=True, null=True)
    can_provide_info = models.BooleanField(default=True)
    last_fiscal_year_end_date = models.DateField(blank=True, null=True)
    total_clients = models.PositiveIntegerField(blank=True, null=True)
    total_employees = models.PositiveIntegerField(blank=True, null=True)
    total_revenue = models.BigIntegerField(blank=True, null=True)
    total_expenses = models.BigIntegerField(blank=True, null=True)
    total_program_expenses = models.BigIntegerField(blank=True, null=True)

    # Registration
    POC_CHOICES = ((0, 'No'), (1, 'Yes'))
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        Organization, related_name='user_history', blank=True, null=True, on_delete=models.SET_NULL
    )
    is_poc = models.BooleanField(choices=POC_CHOICES, default=False)
    is_currently_employed = models.BooleanField(default=False)
    org_admin_email = models.EmailField(blank=True, null=True)

    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(blank=True, null=True)
