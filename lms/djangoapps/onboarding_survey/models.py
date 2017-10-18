"""
Models to support the on-boarding surveys
"""
from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
import logging

from common.lib.nodebb_client.client import NodeBBClient

log = logging.getLogger("edx.onboarding_survey")


class Organization(models.Model):
    """
    Represents an organization.
    """

    name = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True, db_index=True)
    is_poc_exist = models.BooleanField(default=False)

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
    is_currently_employed = models.BooleanField(default=False)
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='extended_profile')
    org_admin_email = models.EmailField(blank=True, null=True)
    is_survey_completed = models.BooleanField(default=False)


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


class OrganizationSurvey(models.Model):
    """
    The model to save the organization survey as provided by the user.
    """
    user = models.OneToOneField(User, unique=True, db_index=True, related_name='organization_survey', null=True, blank=True)
    role_in_org = models.ForeignKey(
        RoleInsideOrg, on_delete=models.CASCADE, related_name='org_survey', blank=True, null=True
    )
    start_month_year = models.CharField(max_length=100, blank=True)

    country = models.CharField(max_length=256)
    city = models.CharField(max_length=265, blank=True)
    url = models.URLField(max_length=256, blank=True)

    sector = models.ForeignKey(OrgSector, on_delete=models.CASCADE, related_name='org_survey')
    level_of_operation = models.ForeignKey(OperationLevel, on_delete=models.CASCADE, related_name='org_survey')
    focus_area = models.ForeignKey(FocusArea, on_delete=models.CASCADE, related_name='org_survey')

    founding_year = models.PositiveSmallIntegerField(blank=True, null=True)
    total_employees = models.ForeignKey(
        TotalEmployee, on_delete=models.CASCADE, related_name='org_survey', blank=True, null=True
    )
    total_volunteers = models.ForeignKey(
        TotalVolunteer, on_delete=models.CASCADE, related_name='org_survey', blank=True, null=True
    )

    total_clients = models.PositiveIntegerField(blank=True, null=True)
    total_revenue = models.CharField(max_length=255, blank=True)
    partner_network = models.ForeignKey(
        PartnerNetwork, on_delete=models.CASCADE, related_name='org_survey', blank=True, null=True
    )


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
    capacity_areas = models.ManyToManyField(OrganizationalCapacityArea)
    interested_communities = models.ManyToManyField(CommunityTypeInterest)
    reason_of_selected_interest = models.CharField(max_length=255, blank=True)
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


class UserInfoSurvey(models.Model):
    """
    The survey to store the basic information about the user.
    """
    user = models.OneToOneField(
        User, unique=True, db_index=True, related_name='user_info_survey', null=True, blank=True
    )
    dob = models.DateField(blank=True, null=True)

    level_of_education = models.ForeignKey(
        EducationLevel, on_delete=models.CASCADE, related_name='user_info_survey', blank=True, null=True
    )

    language = models.CharField(max_length=256)

    english_proficiency = models.ForeignKey(EnglishProficiency, on_delete=models.CASCADE, related_name='user_info_survey')

    country_of_residence = models.CharField(max_length=256)
    city_of_residence = models.CharField(max_length=256, blank=True)

    is_emp_location_different = models.BooleanField(default=False)

    country_of_employment = models.CharField(max_length=256, blank=True)
    city_of_employment = models.CharField(max_length=256, blank=True)


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True)
    # CommunityTypeInterest
    coi_similar_org = models.BooleanField(blank=True, default=False)
    coi_similar_org_capacity = models.BooleanField(blank=True, default=False)
    coi_same_region = models.BooleanField(blank=True, default=False)
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
    # OrgCapacityArea
    org_capacity_logistics = models.BooleanField(blank=True, default=False)
    org_capacity_administration = models.BooleanField(blank=True, default=False)
    org_capacity_finance = models.BooleanField(blank=True, default=False)
    org_capacity_external_relation = models.BooleanField(blank=True, default=False)
    org_capacity_program = models.BooleanField(blank=True, default=False)
    org_capacity_leadership = models.BooleanField(blank=True, default=False)
    # PartnerNetwork
    partner_network = models.ForeignKey(
        PartnerNetwork, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )
    # PersonalGoal
    goal_gain_new_skill = models.BooleanField(blank=True, default=False)
    goal_relation_with_other = models.BooleanField(blank=True, default=False)
    goal_develop_leadership = models.BooleanField(blank=True, default=False)
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
    # TotalVolunteers
    org_total_volunteers = models.ForeignKey(
        TotalVolunteer, on_delete=models.SET_NULL, related_name='user_history', blank=True, null=True
    )
    # UserInfoSurvey
    dob = models.DateField(blank=True, null=True)
    language = models.CharField(max_length=255)
    country_of_residence = models.CharField(max_length=255)
    city_of_residence = models.CharField(max_length=255, blank=True)
    is_emp_location_different = models.BooleanField(default=False)
    country_of_employment = models.CharField(max_length=255, blank=True)
    city_of_employment = models.CharField(max_length=255, blank=True)
    # InterestSurvey
    reason_of_selected_interest = models.CharField(max_length=255, blank=True)
    # OrganizationSurvey
    org_start_month_year = models.CharField(max_length=100, blank=True)
    org_country = models.CharField(max_length=255)
    org_city = models.CharField(max_length=255, blank=True)
    org_url = models.URLField(max_length=255, blank=True)
    org_founding_year = models.PositiveSmallIntegerField(blank=True, null=True)
    org_total_clients = models.PositiveIntegerField(blank=True, null=True)
    org_total_revenue = models.CharField(max_length=255, blank=True)
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


@receiver(models.signals.post_save, sender=UserInfoSurvey)
@receiver(models.signals.post_save, sender=ExtendedProfile)
def sync_user_info_with_nodebb(sender, instance, **kwargs):  # pylint: disable=unused-argument, invalid-name
    """ Sync user information with  """
    user = instance.user

    if user:
        try:
            extended_profile = user.extended_profile
            user_info_survey = user.user_info_survey
        except UserInfoSurvey.DoesNotExist:
            return
        except ExtendedProfile.DoesNotExist:
            return

        data_to_sync = {
            "_uid": 1,
            "first_name": extended_profile.first_name,
            "last_name": extended_profile.last_name,
            "city_of_residence": user_info_survey.city_of_residence,
            "country_of_residence": user_info_survey.country_of_residence
        }

        status_code, response_body = NodeBBClient().users.update_profile(user.username, kwargs=data_to_sync)

        if status_code != 200:
            log.error(
                "Error: Can not update user({}) on nodebb due to {}".format(user.username, response_body)
            )
        else:
            log.info('Success: User({}) has been updated on nodebb'.format(user.username))
