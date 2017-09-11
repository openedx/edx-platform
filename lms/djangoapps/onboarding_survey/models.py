"""
Models to support the on-boarding surveys
"""
from django.db import models
from django.contrib.auth.models import User


class RoleInsideOrg(models.Model):
    """
    Specifies what is the role of a user inside the organization.
    """
    role = models.CharField(max_length=256)

    def __str__(self):
        return self.role


class OrgSector(models.Model):
    """
    Specifies what sector the organization is working in.
    """
    sector = models.CharField(max_length=256)

    def __str__(self):
        return self.sector


class OperationLevel(models.Model):
    """
    Specifies the level of organization like national, international etc.
    """
    level = models.CharField(max_length=256)

    def __str__(self):
        return self.level


class FocusArea(models.Model):
    """
    The are of focus of an organization.
    """
    area = models.CharField(max_length=256)

    def __str__(self):
        return self.area


class TotalEmployee(models.Model):
    """
    Total employees in an organization.
    """
    total = models.CharField(max_length=256)

    def __str__(self):
        return self.total


class TotalVolunteer(models.Model):
    """
    Total volunteers in an organization.
    """
    total = models.CharField(max_length=256)

    def __str__(self):
        return self.total


class PartnerNetwork(models.Model):
    """
    Specifies about the partner network being used in an organization.
    """
    network = models.CharField(max_length=256)

    is_partner_affiliated = models.BooleanField(default=False)

    def __str__(self):
        return self.network


class OrganizationSurvey(models.Model):
    """
    The model to save the organization survey as provided by the user.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='organization_survey', null=True, blank=True)
    role_in_org = models.ForeignKey(RoleInsideOrg, on_delete=models.CASCADE, related_name='org_survey')
    state_mon_year = models.CharField(max_length=100)

    country = models.CharField(max_length=256)
    city = models.CharField(max_length=265)
    url = models.URLField(max_length=256)

    sector = models.ForeignKey(OrgSector, on_delete=models.CASCADE, related_name='org_survey')
    level_of_op = models.ForeignKey(OperationLevel, on_delete=models.CASCADE, related_name='org_survey')
    focus_area = models.ForeignKey(FocusArea, on_delete=models.CASCADE, related_name='org_survey')

    founding_year = models.PositiveSmallIntegerField()
    total_employees = models.ForeignKey(TotalEmployee, on_delete=models.CASCADE, related_name='org_survey')
    total_volunteers = models.ForeignKey(TotalVolunteer, on_delete=models.CASCADE, related_name='org_survey')

    total_annual_clients_or_beneficiary = models.PositiveIntegerField()
    total_annual_revenue_for_last_fiscal = models.CharField(max_length=256)
    partner_network = models.ForeignKey(PartnerNetwork, on_delete=models.CASCADE, related_name='org_survey')


class OrganizationalCapacityArea(models.Model):
    """
    Capacity are an Organization. This will be used in Interests survey.
    """

    capacity_area = models.CharField(max_length=256)

    def __str__(self):
        return self.capacity_area


class CommunityTypeInterest(models.Model):
    """
    The model to used to get info from user about the type of community he/she
    would like to be added. E.g. community according to region, country etc.
    """
    community_type = models.CharField(max_length=256)

    def __str__(self):
        return self.community_type


class PersonalGoal(models.Model):
    """
    Models user's goal behind joining the platform.
    """
    goal = models.CharField(max_length=256)

    def __str__(self):
        return self.goal


class InterestsSurvey(models.Model):
    """
    The model to store the interests survey as provided by the user.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='interest_survey', null=True, blank=True)
    capacity_areas = models.ManyToManyField(OrganizationalCapacityArea)
    interested_communities = models.ManyToManyField(CommunityTypeInterest)
    reason_of_interest = models.CharField(max_length=256, blank=True)
    personal_goal = models.ManyToManyField(PersonalGoal)


class EducationLevel(models.Model):
    """
    Models education level of the user
    """
    level = models.CharField(max_length=256)

    def __str__(self):
        return self.level


class EnglishProficiency(models.Model):
    """
    Models english proficiency level of the user.
    """
    proficiency = models.CharField(max_length=256)

    def __str__(self):
        return self.proficiency


class UserInfoSurvey(models.Model):
    """
    The survey to store the basic information about the user.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='user_info_survey', null=True, blank=True)
    dob = models.DateField()

    level_of_education = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name='user_info_survey')

    language = models.CharField(max_length=256)

    english_prof = models.ForeignKey(EnglishProficiency, on_delete=models.CASCADE, related_name='user_info_survey')

    country_of_residence = models.CharField(max_length=256)
    city_of_residence = models.CharField(max_length=256)

    is_country_or_city_different = models.BooleanField(default=False)

    country_of_employment = models.CharField(max_length=256, blank=True)
    city_of_employment = models.CharField(max_length=256, blank=True)
