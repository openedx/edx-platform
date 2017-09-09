from django.db import models
from django.contrib.auth.models import User


class RoleInsideOrg(models.Model):
    role = models.CharField(max_length=256)

    def __str__(self):
        return self.role


class OrgSector(models.Model):
    sector = models.CharField(max_length=256)

    def __str__(self):
        return self.sector


class OperationLevel(models.Model):
    level = models.CharField(max_length=256)

    def __str__(self):
        return self.level


class FocusArea(models.Model):
    area = models.CharField(max_length=256)

    def __str__(self):
        return self.area


class TotalEmployee(models.Model):
    total = models.CharField(max_length=256)

    def __str__(self):
        return self.total


class TotalVolunteer(models.Model):
    total = models.CharField(max_length=256)

    def __str__(self):
        return self.total


class PartnerNetwork(models.Model):
    network = models.CharField(max_length=256)

    is_partner_affiliated = models.BooleanField(default=False)

    def __str__(self):
        return self.network


class OrganizationSurvey(models.Model):
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
    capacity_area = models.CharField(max_length=256)

    def __str__(self):
        return self.capacity_area


class CommunityTypeInterest(models.Model):
    community_type = models.CharField(max_length=256)

    def __str__(self):
        return self.community_type


class InclusionInCommunityChoice(models.Model):
    choice = models.CharField(max_length=256)

    def __str__(self):
        return self.choice


class PersonalGoal(models.Model):
    goal = models.CharField(max_length=256)

    def __str__(self):
        return self.goal


class InterestsSurvey(models.Model):
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='interest_survey', null=True, blank=True)
    capacity_areas = models.ManyToManyField(OrganizationalCapacityArea)
    interested_communities = models.ManyToManyField(CommunityTypeInterest)
    # inclusion_in_community = models.ForeignKey(
    #     InclusionInCommunityChoice, on_delete=models.CASCADE, related_name='interest_survey'
    # )
    reason_of_interest = models.CharField(max_length=256, blank=True)
    personal_goal = models.ManyToManyField(PersonalGoal)


class EducationLevel(models.Model):
    level = models.CharField(max_length=256)

    def __str__(self):
        return self.level


class EnglishProficiency(models.Model):
    proficiency = models.CharField(max_length=256)

    def __str__(self):
        return self.proficiency


class UserInfoSurvey(models.Model):
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






