import logging
import re
import uuid
from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, URLValidator
from django.db import models
from django.utils.translation import ugettext_noop
from model_utils.models import TimeStampedModel
from multiselectfield import MultiSelectField
from pytz import utc

import choices
from constants import (
    NOT_INTERESTED_KEY,
    NOT_INTERESTED_VAL,
    ORG_PARTNERSHIP_END_DATE_PLACEHOLDER,
    REMIND_ME_LATER_KEY,
    REMIND_ME_LATER_VAL,
    TAKE_ME_THERE_KEY,
    TAKE_ME_THERE_VAL
)
from openedx.features.custom_fields.multiselect_with_other.db.fields import MultiSelectWithOtherField

log = logging.getLogger("edx.onboarding")


class SchemaOrNoSchemaURLValidator(URLValidator):
    regex = re.compile(
        r'((([A-Za-z]{3,9}:(?:\/\/)?)(?:[-;:&=\+\$,\w]+@)?[A-Za-z0-9.-]'
        r'+|(?:www.|[-;:&=\+\$,\w]+@)[A-Za-z0-9.-]+)((?:\/[\+~%\/.\w-]*)'
        r'?\??(?:[-\+=&;%@.\w_]*)#?(?:[\w]*))?)',
        re.IGNORECASE
    )


class OrgSectorManager(models.Manager):
    """Custom manager to get choices of org sector"""

    def get_choices(self):
        return [(org_sector.code, org_sector.label) for org_sector in OrgSector.objects.all()]

    def get_map(self):
        return {org_sector.code: org_sector.label for org_sector in OrgSector.objects.all()}


class OrgSector(models.Model):
    """
    Specifies what sector the organization is working in.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    objects = OrgSectorManager()

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

    @classmethod
    def get_map(cls):
        return {fa.code: fa.label for fa in cls.objects.all()}

    class Meta:
        ordering = ['order']


class TotalEmployeeManager(models.Manager):
    """Custom manager to get choices of number of employees range"""

    def get_choices(self):
        return [(total_emp.code, total_emp.label) for total_emp in TotalEmployee.objects.all()]


class TotalEmployee(models.Model):
    """
    Total employees in an organization.
    """
    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=256)

    objects = TotalEmployeeManager()

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class PartnerNetwork(models.Model):
    """
    Specifies about the partner network being used in an organization.
    """

    NON_PROFIT_ORG_TYPE_CODE = "NPORG"

    order = models.SmallIntegerField(unique=True, null=True)
    code = models.CharField(max_length=10, unique=True)
    label = models.CharField(max_length=255)

    is_partner_affiliated = models.BooleanField(default=False)

    show_opt_in = models.BooleanField(default=False)
    affiliated_name = models.CharField(max_length=32, null=True, blank=True)
    program_name = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ['order']


class Currency(models.Model):
    country = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    alphabetic_code = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    minor_units = models.CharField(max_length=255)

    def __str__(self):
        return "%s %s %s" % (self.country, self.name, self.alphabetic_code if self.alphabetic_code else "N/A")


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
    is_organization_registered = models.CharField(
        max_length=20, blank=True, null=True, verbose_name='Is Organization Registered as 501c3?'
    )

    alternate_admin_email = models.EmailField(blank=True, null=True)

    # If organization has affiliation with some affiliated partners,
    # this flag will be True
    has_affiliated_partner = models.BooleanField(default=False)

    def users_count(self):
        """
        :return: Users count in an organization
        """
        return UserExtendedProfile.objects.filter(organization=self).count()

    def can_join_as_first_learner(self, exclude_user):
        """
        Identify, if next user, who will join this organization will become first learner not not.

        :param exclude_user: Currently logged-in user
        :return: True if this organization is not associated with any
         user, except currently logged-in user; False otherwise
        """
        users_in_org = UserExtendedProfile.objects.filter(organization=self).exclude(user=exclude_user)
        return not users_in_org.exists()

    @staticmethod
    def is_non_profit(user_extended_profile):
        """
        :return: Organization NP status
        """
        return True if user_extended_profile.organization and \
            user_extended_profile.organization.org_type == PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE else False

    def admin_info(self):
        """
        :return: Information about the current admin of organization
        """
        return "%s" % self.admin.email if self.admin else "Administrator not assigned yet."

    @property
    def first_learner(self):
        """
        :return: organization's first learner
        """
        org_first_learner = self.extended_profile.filter(is_first_learner=True).first()
        return org_first_learner.user if org_first_learner else None

    def get_active_partners(self):
        """ Return list of active organization partners"""
        return self.organization_partners.filter(end_date__gt=datetime.utcnow()).values_list('partner', flat=True)

    def hubspot_data(self):
        """
        Create data for sync with HubSpot.
        """
        org_label = self.label
        org_type = OrgSector.objects.get_map().get(self.org_type, "")
        focus_area = FocusArea.get_map().get(self.focus_area, "")
        return org_label, org_type, focus_area

    def __unicode__(self):
        return self.label


class OrganizationPartner(models.Model):
    """
    The model to save the organization partners.
    """
    organization = models.ForeignKey(Organization, related_name='organization_partners')
    partner = models.CharField(max_length=10)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __unicode__(self):
        return "%s - %s" % (self.organization, self.partner)

    @classmethod
    def update_organization_partners(cls, organization, partners, removed_partners):
        """
        Add/Update partners data or an organization
        """

        # Set unchecked partners end date to today
        cls.objects.filter(
            organization=organization,
            partner__in=removed_partners, end_date__gt=datetime.utcnow()
        ).update(end_date=datetime.now(utc))

        # Mark removed partner affliation flag to False if not selected in any organization
        _removed_partners = PartnerNetwork.objects.filter(code__in=removed_partners)
        for partner in _removed_partners:
            p = cls.objects.filter(partner=partner.code).first()
            if not p:
                partner.is_partner_affiliated = False
                partner.save()

        # Get already added partners for an organization
        no_updated_selections = cls.objects.filter(
            organization=organization,
            partner__in=partners, end_date__gt=datetime.utcnow()
        ).values_list('partner', flat=True)

        # Filter out new/reselected Partners
        new_selections = [p for p in partners if p not in no_updated_selections]
        _partners = PartnerNetwork.objects.filter(code__in=new_selections)

        # Add new/reselected Partners and mark network as affiliated
        lst_to_create = []
        for partner in _partners:
            start_date = datetime.now()
            end_date = ORG_PARTNERSHIP_END_DATE_PLACEHOLDER
            obj = cls(organization=organization, partner=partner.code, start_date=start_date, end_date=end_date)
            lst_to_create.append(obj)

        cls.objects.bulk_create(lst_to_create)
        _partners.update(is_partner_affiliated=True)

        # Check if organization has any active grantee partners
        opted_partners = PartnerNetwork.objects.filter(
            show_opt_in=True
        ).values_list('code', flat=True)
        org_active_partners = organization.get_active_partners()
        has_affiliated_partner = True if list(set(opted_partners) & set(org_active_partners)) else False

        organization.has_affiliated_partner = has_affiliated_partner
        organization.save()


class GranteeOptIn(models.Model):
    agreed = models.BooleanField()
    organization_partner = models.ForeignKey(OrganizationPartner, related_name='grantee_opt_in')
    user = models.ForeignKey(User, related_name='grantee_opt_in')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s-%s' % (self.user, self.created_at)


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
    suggested_admin_email = models.EmailField()
    is_hash_consumed = models.BooleanField(default=False)
    activation_hash = models.CharField(max_length=32)

    def __str__(self):
        return "%s-%s" % (self.suggested_admin_email, self.activation_hash)

    @classmethod
    def assign_hash(cls, organization, suggested_by, suggested_admin_email):
        """
        Link a hash key to a user for administrator role confirmation
        """
        return cls.objects.create(organization=organization, suggested_by=suggested_by,
                                  suggested_admin_email=suggested_admin_email, activation_hash=uuid.uuid4().hex)


class UserExtendedProfile(TimeStampedModel):
    """
    Extra profile fields that we don't want to enter in user_profile to avoid code conflicts at edx updates
    """

    SURVEYS_LIST = ["user_info", "interests", "organization", "org_detail_survey"]

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
                                                 validators=[MaxValueValidator(168)], null=True)

    is_interests_data_submitted = models.BooleanField(default=False)
    is_organization_metrics_submitted = models.BooleanField(default=False)
    is_first_learner = models.BooleanField(default=False)
    is_alquity_user = models.BooleanField(default=False)

    hear_about_philanthropyu = MultiSelectWithOtherField(choices=choices.HEAR_ABOUT_PHILANTHROPY,
                                                         other_max_length=255,
                                                         max_choices=1,
                                                         blank=True)
    function_areas = MultiSelectField(choices=choices.FUNCTIONS, blank=True)
    interests = MultiSelectField(choices=choices.INTERESTS, blank=True)
    learners_related = MultiSelectField(choices=choices.INTERESTED_LEARNERS, blank=True)
    goals = MultiSelectField(choices=choices.GOALS, blank=True)
    hubspot_contact_id = models.CharField(max_length=20, null=True)

    def __str__(self):
        return str(self.user)

    def get_user_selected_functions(self, _type='labels'):
        """
        :return: Users selected function areas
        :param _type: labels / fields
        :return: list of labels / names of fields
        """
        if _type == 'labels':
            return map(choices.FUNCTIONS_DICT.get, self.function_areas)

        return list(self.function_areas)

    def get_user_selected_interests(self, _type='labels'):
        """
        :return: Users selected interest
        :param _type: labels / fields
        :return: list of labels / names of fields
        """
        if _type == 'labels':
            return map(choices.INTERESTS_DICT.get, self.interests)

        return list(self.interests)

    def is_organization_data_filled(self):
        """
        Return status for registration third step completion
        """
        return self.organization.org_type and self.organization.focus_area and self.organization.level_of_operation \
            and self.organization.total_employees

    def is_organization_details_filled(self):
        """
        :return: Status for registration fourth step completion
        """
        return self.is_organization_metrics_submitted

    def get_normal_user_attend_surveys(self):
        """
        :return: List of attended surveys that a simple learner can attend
        """
        attended_list = []

        if (not self.organization and self.user.profile.level_of_education and self.english_proficiency) or (
                self.organization and self.user.profile.level_of_education and self.start_month_year and
                self.english_proficiency):
            attended_list.append(self.SURVEYS_LIST[0])
        if self.is_interests_data_submitted:
            attended_list.append(self.SURVEYS_LIST[1])

        return attended_list

    def get_admin_or_first_user_attend_surveys(self):
        """
        :return: List of attended surveys that a first learner OR admin can attend
        """
        attended_list = self.get_normal_user_attend_surveys()

        if self.is_organization_data_filled():
            attended_list.append(self.SURVEYS_LIST[2])
        if self.is_organization_details_filled() \
                and self.organization.org_type == PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE:
            attended_list.append(self.SURVEYS_LIST[3])

        return attended_list

    def surveys_to_attend(self):
        """
        :return: List of survey for a user to attend depending on the user type (admin/first user in org/non-admin)
        """
        surveys_to_attend = self.SURVEYS_LIST[:2]
        if self.organization and (self.is_organization_admin or self.is_first_signup_in_org):
            surveys_to_attend = self.SURVEYS_LIST[:3]

        if self.organization and self.organization.org_type == PartnerNetwork.NON_PROFIT_ORG_TYPE_CODE \
                and (self.is_organization_admin or self.is_first_signup_in_org):
            surveys_to_attend = self.SURVEYS_LIST

        return surveys_to_attend

    def attended_surveys(self):
        """
        :return: List of user's attended on-boarding surveys
        """

        if not (self.organization and (self.is_organization_admin or self.is_first_signup_in_org)):
            attended_list = self.get_normal_user_attend_surveys()
        else:
            attended_list = self.get_admin_or_first_user_attend_surveys()

        return attended_list

    def unattended_surveys(self, _type="map"):
        """
        :return: Mapping of user's unattended on-boarding surveys
        """

        surveys_to_attend = self.surveys_to_attend()

        if _type == "list":
            return [s for s in surveys_to_attend if s not in self.attended_surveys()]

        return {s: True if s in self.attended_surveys() else False for s in surveys_to_attend}

    @property
    def is_organization_admin(self):
        """
        :return: User organization administration status
        """
        if self.organization:
            return self.user == self.organization.admin

        return False

    def admin_has_pending_admin_suggestion_request(self):
        pending_suggestion_request = OrganizationAdminHashKeys.objects.filter(organization=self.organization,
                                                                              suggested_by=self.user,
                                                                              is_hash_consumed=False).first()
        return bool(self.is_organization_admin and pending_suggestion_request)

    @property
    def is_first_signup_in_org(self):
        """
        :return: User is first learner OR not
        """
        return self.is_first_learner

    def has_submitted_oef(self):
        """
        :return: User has taken OEF OR not
        """
        taken_oef = False

        if self.organization:
            taken_oef = bool(self.user.organization_oef_scores.filter(org=self.organization, user=self.user).exclude(
                finish_date__isnull=True))

        return self.organization and taken_oef


class EmailPreference(TimeStampedModel):
    user = models.OneToOneField(User, related_name="email_preferences")
    opt_in = models.CharField(max_length=5, default=None, null=True, blank=True)

    def __str__(self):
        return "%s %s" % (self.user.email, self.opt_in)


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
    actual_data = models.NullBooleanField(choices=ACTUAL_DATA_CHOICES, blank=True, null=True)
    effective_date = models.DateField(blank=True, null=True)
    total_clients = models.PositiveIntegerField(blank=True, null=True)
    total_employees = models.PositiveIntegerField(blank=True, null=True)
    local_currency = models.CharField(max_length=10, blank=True, null=True)
    total_revenue = models.BigIntegerField(blank=True, null=True)
    total_donations = models.BigIntegerField(blank=True, null=True)
    total_expenses = models.BigIntegerField(blank=True, null=True)
    total_program_expenses = models.BigIntegerField(blank=True, null=True)


class OrganizationMetricUpdatePrompt(models.Model):
    org = models.ForeignKey(Organization, related_name="organization_metrics_update_prompts")
    responsible_user = models.ForeignKey(User, related_name="organization_metrics_update_prompts")
    latest_metric_submission = models.DateTimeField()
    year = models.BooleanField(default=False)
    year_month = models.BooleanField(default=False)
    year_three_month = models.BooleanField(default=False)
    year_six_month = models.BooleanField(default=False)
    # None(Python)/Null(MySQL): we can remind learner, True: learner clicked `Remind Me Later`,
    # False:  learner clicked `No Thanks`
    remind_me_later = models.NullBooleanField()

    def __unicode__(self):
        return '{}, {}'.format(self.responsible_user.username, self.org.label.encode('utf-8'))


class MetricUpdatePromptRecord(TimeStampedModel):
    prompt = models.ForeignKey(OrganizationMetricUpdatePrompt, on_delete=models.CASCADE,
                               related_name="metrics_update_prompt_records")
    CLICK_CHOICES = (
        (REMIND_ME_LATER_KEY, ugettext_noop(REMIND_ME_LATER_VAL)),
        (TAKE_ME_THERE_KEY, ugettext_noop(TAKE_ME_THERE_VAL)),
        (NOT_INTERESTED_KEY, ugettext_noop(NOT_INTERESTED_VAL))
    )
    click = models.CharField(
        null=True, max_length=3, db_index=True, choices=CLICK_CHOICES
    )


class Education(TimeStampedModel):
    """
    Model to store user education information
    """
    linkedin_id = models.IntegerField(null=True, blank=True, unique=True)
    user = models.ForeignKey(User, related_name='education', on_delete=models.CASCADE)
    school_name = models.CharField(max_length=255, null=True, blank=True)
    degree_name = models.CharField(max_length=255, null=True, blank=True)
    start_month_year = models.DateField(null=True, blank=True)
    end_month_year = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return '{} {}'.format(self.school_name, self.degree_name)


class Experience(TimeStampedModel):
    """
    Model to store user experience information
    """
    linkedin_id = models.IntegerField(null=True, blank=True, unique=True)
    user = models.ForeignKey(User, related_name='experience', on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    title = models.CharField(max_length=255, null=True, blank=True)
    company = models.CharField(max_length=255, null=True, blank=True)
    summary = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.title


class Skill(TimeStampedModel):
    """
    Model to store user skill information
    """
    linkedin_id = models.IntegerField(null=True, blank=True, unique=True)
    user = models.ForeignKey(User, related_name='skill', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name
