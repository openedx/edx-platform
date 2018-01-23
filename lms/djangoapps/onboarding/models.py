import logging
import uuid

import re
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.contrib.auth.models import User
from simple_history import register
from model_utils.models import TimeStampedModel
from simple_history.models import HistoricalRecords
from django.core.validators import MaxValueValidator, URLValidator
from django.db import models

from student.models import UserProfile

log = logging.getLogger("edx.onboarding")


class SchemaOrNoSchemaURLValidator(URLValidator):
    regex = re.compile(
        r'((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]'
        r'+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w-]*)'
        r'?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)',
        re.IGNORECASE
    )

# register User and UserProfile models for django-simple-history module
register(User, app='lms.djangoapps.onboarding', table_name='auth_historicaluser')
register(UserProfile, table_name='auth_historicaluserprofile')


class OrgSector(models.Model):
    """
    Specifies what sector the organization is working in.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class OperationLevel(models.Model):
    """
    Specifies the level of organization like national, international etc.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class FocusArea(models.Model):
    """
    The are of focus of an organization.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class TotalEmployee(models.Model):
    """
    Total employees in an organization.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class PartnerNetwork(models.Model):
    """
    Specifies about the partner network being used in an organization.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=255)

    is_partner_affiliated = models.BooleanField(default=False)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class Currency(models.Model):
    name = models.CharField(max_length=255)
    alphabetic_code = models.CharField(max_length=255)


class EducationLevel(models.Model):
    """
    Models education level of the user
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class EnglishProficiency(models.Model):
    """
    Models english proficiency level of the user.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class FunctionArea(models.Model):
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=255)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class Organization(TimeStampedModel):
    """
    Represents an organization.
    """

    label = models.CharField(max_length=255, db_index=True)
    admin = models.ForeignKey(User, related_name='organization', blank=True, null=True, on_delete=models.SET_NULL)
    country = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    unclaimed_org_admin_email = models.EmailField(unique=True, blank=True, null=True)
    url = models.URLField(max_length=255, blank=True, null=True, validators=[SchemaOrNoSchemaURLValidator])
    founding_year = models.PositiveSmallIntegerField(blank=True, null=True)
    registration_number = models.CharField(max_length=30, blank=True, null=True)

    org_type = models.CharField(max_length=10, blank=True, null=True)
    level_of_operation = models.CharField(max_length=10, blank=True, null=True)
    focus_area = models.CharField(max_length=10, blank=True, null=True)
    total_employees = models.CharField(max_length=10, blank=True, null=True)

    alternate_admin_email = models.EmailField(blank=True, null=True)

    history = HistoricalRecords()

    def is_first_signup_in_org(self):
        return UserExtendedProfile.objects.filter(organization=self).count() == 1

    def __str__(self):
        return self.label


class OrganizationPartner(models.Model):
    """
    The model to save the organization partners.
    """
    organization = models.ForeignKey(Organization, related_name='organization_partners')
    partner = models.CharField(max_length=10)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    @classmethod
    def update_organization_partners(cls, organization, partners):
        cls.objects.filter(organization=organization).delete()

        _partners = PartnerNetwork.objects.filter(code__in=partners)

        lst_to_create = []
        for partner in _partners:
            start_date = datetime.now()
            end_date = start_date + relativedelta(years=100)
            obj = cls(organization=organization, partner=partner.code, start_date=start_date, end_date=end_date)
            lst_to_create.append(obj)

        cls.objects.bulk_create(lst_to_create)
        _partners.update(is_partner_affiliated=True)


class RoleInsideOrg(models.Model):
    """
    Specifies what is the role of a user inside the organization.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class OrganizationAdminHashKeys(TimeStampedModel):
    """
    Model to hold hash keys for users that are suggested as admin for an organization
    """
    organization = models.ForeignKey(Organization, related_name='suggested_admins')
    suggested_by = models.ForeignKey(User)
    suggested_admin_email = models.EmailField(unique=True)
    is_hash_consumed = models.BooleanField(default=False)
    activation_hash = models.CharField(max_length=32)

    def __str__(self):
        return "%s-%s" % (self.suggested_admin_email, self.activation_key_for_admin)

    @classmethod
    def assign_hash(cls, organization, suggested_by, suggested_admin_email):
        return cls.objects.create(organization=organization, suggested_by=suggested_by,
                                  suggested_admin_email=suggested_admin_email, activation_hash=uuid.uuid4().hex)


class UserExtendedProfile(TimeStampedModel):
    """
    Extra profile fields that we don't want to enter in user_profile to avoid code conflicts at edx updates
    """

    SURVEYS_LIST = ["user_info", "interests", "organization", "org_detail_survey"]

    FUNCTIONS_LABELS = {
        "0=function_strategy_planning": "Strategy and planning",
        "1=function_leadership_governance": "Leadership and governance",
        "2=function_program_design": "Program design and development",
        "3=function_measurement_eval": "Measurement, evaluation, and learning",
        "4=function_stakeholder_engagement": "Stakeholder engagement and partnerships",
        "5=function_human_resource": "Human resource management",
        "6=function_financial_management": "Financial management",
        "7=function_fundraising": "Fundraising and resource mobilization",
        "8=function_marketing_communication": "Marketing, communications, and PR",
        "9=function_system_tools": "Systems, tools, and processes",
    }

    INTERESTS_LABELS = {
        "0=interest_strategy_planning": "Strategy and planning",
        "1=interest_leadership_governance": "Leadership and governance",
        "2=interest_program_design": "Program design and development",
        "3=interest_measurement_eval": "Measurement, evaluation, and learning",
        "4=interest_stakeholder_engagement": "Stakeholder engagement and partnerships",
        "5=interest_human_resource": "Human resource management",
        "6=interest_financial_management": "Financial management",
        "7=interest_fundraising": "Fundraising and resource mobilization",
        "8=interest_marketing_communication": "Marketing, communications, and PR",
        "9=interest_system_tools": "Systems, tools, and processes",
    }

    INTERESTED_LEARNERS_LABELS = {
        "0=learners_same_region": "Learners from my region or country",
        "1=learners_similar_oe_interest": "Learners interested in same areas of organization effectiveness",
        "2=learners_similar_org": "Learners working for similar organizations",
        "3=learners_diff_who_are_different": "Learners who are different from me"
    }

    GOALS_LABELS = {
        "0=goal_contribute_to_org": "Help improve my organization",
        "1=goal_gain_new_skill": "Develop new skills",
        "2=goal_improve_job_prospect": "Get a job",
        "3=goal_relation_with_other": "Build relationships with other nonprofit leaders"
    }

    user = models.OneToOneField(User, unique=True, db_index=True, related_name='extended_profile')
    organization = models.ForeignKey(Organization, related_name='extended_profile', blank=True, null=True,
                                     on_delete=models.SET_NULL)
    country_of_employment = models.CharField(max_length=255, null=True)
    not_listed_gender = models.CharField(max_length=255, null=True, blank=True)
    city_of_employment = models.CharField(max_length=255, null=True)
    english_proficiency = models.CharField(max_length=10, null=True)
    start_month_year = models.CharField(max_length=100, null=True)
    role_in_org = models.CharField(max_length=10, null=True)
    hours_per_week = models.PositiveIntegerField("Typical Number of Hours Worked per Week*", default=0,
                                                 validators=[MaxValueValidator(168)])

    # User functions related fields
    function_strategy_planning = models.SmallIntegerField(FUNCTIONS_LABELS["0=function_strategy_planning"], default=0)
    function_leadership_governance = models.SmallIntegerField(FUNCTIONS_LABELS["1=function_leadership_governance"], default=0)
    function_program_design = models.SmallIntegerField(FUNCTIONS_LABELS["2=function_program_design"], default=0)
    function_measurement_eval = models.SmallIntegerField(FUNCTIONS_LABELS["3=function_measurement_eval"], default=0)
    function_stakeholder_engagement = models.SmallIntegerField(FUNCTIONS_LABELS["4=function_stakeholder_engagement"], default=0)
    function_human_resource = models.SmallIntegerField(FUNCTIONS_LABELS["5=function_human_resource"], default=0)
    function_financial_management = models.SmallIntegerField(FUNCTIONS_LABELS["6=function_financial_management"], default=0)
    function_fundraising = models.SmallIntegerField(FUNCTIONS_LABELS["7=function_fundraising"], default=0)
    function_marketing_communication = models.SmallIntegerField(FUNCTIONS_LABELS["8=function_marketing_communication"], default=0)
    function_system_tools = models.SmallIntegerField(FUNCTIONS_LABELS["9=function_system_tools"], default=0)

    # User interests related fields
    interest_strategy_planning = models.SmallIntegerField(INTERESTS_LABELS["0=interest_strategy_planning"], default=0)
    interest_leadership_governance = models.SmallIntegerField(INTERESTS_LABELS["1=interest_leadership_governance"], default=0)
    interest_program_design = models.SmallIntegerField(INTERESTS_LABELS["2=interest_program_design"], default=0)
    interest_measurement_eval = models.SmallIntegerField(INTERESTS_LABELS["3=interest_measurement_eval"], default=0)
    interest_stakeholder_engagement = models.SmallIntegerField(INTERESTS_LABELS["4=interest_stakeholder_engagement"], default=0)
    interest_human_resource = models.SmallIntegerField(INTERESTS_LABELS["5=interest_human_resource"], default=0)
    interest_financial_management = models.SmallIntegerField(INTERESTS_LABELS["6=interest_financial_management"], default=0)
    interest_fundraising = models.SmallIntegerField(INTERESTS_LABELS["7=interest_fundraising"], default=0)
    interest_marketing_communication = models.SmallIntegerField(INTERESTS_LABELS["8=interest_marketing_communication"], default=0)
    interest_system_tools = models.SmallIntegerField(INTERESTS_LABELS["9=interest_system_tools"], default=0)

    # Learners related field
    learners_same_region = models.SmallIntegerField(INTERESTED_LEARNERS_LABELS["0=learners_same_region"],
                                                    default=0)
    learners_similar_oe_interest = models.SmallIntegerField(INTERESTED_LEARNERS_LABELS["1=learners_similar_oe_interest"],
                                                            default=0)
    learners_similar_org = models.SmallIntegerField(INTERESTED_LEARNERS_LABELS["2=learners_similar_org"], default=0)
    learners_diff_who_are_different = models.SmallIntegerField(
        INTERESTED_LEARNERS_LABELS["3=learners_diff_who_are_different"], default=0)

    # User goals related fields
    goal_contribute_to_org = models.SmallIntegerField(GOALS_LABELS["0=goal_contribute_to_org"], default=0)
    goal_gain_new_skill = models.SmallIntegerField(GOALS_LABELS["1=goal_gain_new_skill"], default=0)
    goal_improve_job_prospect = models.SmallIntegerField(GOALS_LABELS["2=goal_improve_job_prospect"], default=0)
    goal_relation_with_other = models.SmallIntegerField(GOALS_LABELS["3=goal_relation_with_other"], default=0)

    is_interests_data_submitted = models.BooleanField(default=False)
    is_organization_metrics_submitted = models.BooleanField(default=False)

    history = HistoricalRecords()

    def __str__(self):
        return self.user

    def get_user_selected_functions(self, _type="labels"):
        if _type == "labels":
            return [label for field_name, label in self.FUNCTIONS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]
        else:
            return [field_name for field_name, label in self.FUNCTIONS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]

    def get_user_selected_interests(self, _type="labels"):
        if _type == "labels":
            return [label for field_name, label in self.INTERESTS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]
        else:
            return [field_name for field_name, label in self.INTERESTS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]

    def get_user_selected_interested_learners(self, _type="labels"):
        if _type == "labels":
            return [label for field_name, label in self.INTERESTED_LEARNERS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]
        else:
            return [field_name for field_name, label in self.INTERESTED_LEARNERS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]

    def get_user_selected_personal_goal(self, _type="labels"):
        if _type == "labels":
            return [label for field_name, label in self.GOALS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]
        else:
            return [field_name for field_name, label in self.GOALS_LABELS.items() if
                    getattr(self, field_name.split("=")[1]) == 1]

    def save_user_function_areas(self, selected_values):
        for function_area_field, label in self.FUNCTIONS_LABELS.items():
            function_area_field = function_area_field.split("=")[1]
            if function_area_field in selected_values:
                _updated_value = 1
            else:
                _updated_value = 0

            self.__setattr__(function_area_field, _updated_value)

    def save_user_interests(self, selected_values):
        for interest_field, label in self.INTERESTS_LABELS.items():
            interest_field = interest_field.split("=")[1]
            if interest_field in selected_values:
                _updated_value = 1
            else:
                _updated_value = 0

            self.__setattr__(interest_field, _updated_value)

    def save_user_interested_learners(self, selected_values):
        for interested_learner_field, label in self.INTERESTED_LEARNERS_LABELS.items():
            interested_learner_field = interested_learner_field.split("=")[1]
            if interested_learner_field in selected_values:
                _updated_value = 1
            else:
                _updated_value = 0

            self.__setattr__(interested_learner_field, _updated_value)

    def is_organization_data_filled(self):
        return self.organization.org_type and self.organization.focus_area and self.organization.level_of_operation \
               and self.organization.total_employees

    def is_organization_details_filled(self):
        return self.is_organization_metrics_submitted

    def save_user_personal_goals(self, selected_values):
        for goal_field, label in self.GOALS_LABELS.items():
            goal_field = goal_field.split("=")[1]
            if goal_field in selected_values:
                _updated_value = 1
            else:
                _updated_value = 0

            self.__setattr__(goal_field, _updated_value)

    def get_normal_user_attend_surveys(self):
        attended_list = []

        if self.user.profile.level_of_education and self.start_month_year and self.english_proficiency:
            attended_list.append(self.SURVEYS_LIST[0])
        if self.is_interests_data_submitted:
            attended_list.append(self.SURVEYS_LIST[1])

        return attended_list

    def get_admin_or_first_user_attend_surveys(self):
        attended_list = self.get_normal_user_attend_surveys()

        if self.is_organization_data_filled():
            attended_list.append(self.SURVEYS_LIST[2])
        if self.is_organization_details_filled():
            attended_list.append(self.SURVEYS_LIST[3])

        return attended_list

    def surveys_to_attend(self):
        surveys_to_attend = self.SURVEYS_LIST[:2]
        if self.organization and (self.is_organization_admin or self.organization.is_first_signup_in_org()):
            surveys_to_attend = self.SURVEYS_LIST

        return surveys_to_attend

    def attended_surveys(self):
        """Return list of user's attended on-boarding surveys"""

        if not (self.organization and (self.is_organization_admin or self.organization.is_first_signup_in_org())):
            attended_list = self.get_normal_user_attend_surveys()
        else:
            attended_list = self.get_admin_or_first_user_attend_surveys()

        return attended_list

    def unattended_surveys(self, _type="map"):
        """Return maping of user's unattended on-boarding surveys"""

        surveys_to_attend = self.surveys_to_attend()

        if _type == "list":
            return [s for s in surveys_to_attend if s not in self.attended_surveys()]

        return {s: True if s in self.attended_surveys() else False for s in surveys_to_attend}

    @property
    def is_organization_admin(self):
        if self.organization:
            return self.user == self.organization.admin

        return False


class OrganizationMetric(TimeStampedModel):
    """
    Model to save organization metrics
    """
    ACTUAL_DATA_CHOICES = (
        (0, "Estimated - My answers are my best guesses based on my knowledge of the organization"),
        (1, "Actual - My answers come directly from my organization's official documentation")
    )

    org = models.ForeignKey(Organization, related_name="organization_metrics")
    user = models.ForeignKey(User, related_name="organization_metrics")
    submission_date = models.DateTimeField(auto_now_add=True)
    actual_data= models.NullBooleanField(choices=ACTUAL_DATA_CHOICES, blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    total_clients = models.PositiveIntegerField(blank=True, null=True)
    total_employees = models.PositiveIntegerField(blank=True, null=True)
    local_currency = models.CharField(max_length=10, blank=True, null=True)
    total_revenue = models.BigIntegerField(blank=True, null=True)
    total_donations = models.BigIntegerField(blank=True, null=True)
    total_expenses = models.BigIntegerField(blank=True, null=True)
    total_program_expenses = models.BigIntegerField(blank=True, null=True)



