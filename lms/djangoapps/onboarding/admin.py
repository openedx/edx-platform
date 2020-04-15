from django.contrib import admin


# import handlers to make sure that they are executed
import onboarding.handlers


from lms.djangoapps.onboarding.models import (
    Currency,
    Education,
    EducationLevel,
    EmailPreference,
    EnglishProficiency,
    Experience,
    FocusArea,
    FunctionArea,
    GranteeOptIn,
    MetricUpdatePromptRecord,
    OperationLevel,
    OrgSector,
    Organization,
    OrganizationMetric,
    OrganizationMetricUpdatePrompt,
    OrganizationPartner,
    PartnerNetwork,
    RoleInsideOrg,
    Skill,
    TotalEmployee,
    UserExtendedProfile
)


class BaseDropdownOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'code', 'label',)


class RoleInsideOrgAdmin(BaseDropdownOrderAdmin):
    pass


class OrgSectorAdmin(BaseDropdownOrderAdmin):
    pass


class OperationLevelAdmin(BaseDropdownOrderAdmin):
    pass


class FocusAreaAdmin(BaseDropdownOrderAdmin):
    pass


class TotalEmployeeAdmin(BaseDropdownOrderAdmin):
    pass


class PartnerNetworkAdmin(BaseDropdownOrderAdmin):
    list_display = ('order', 'code', 'label', 'is_partner_affiliated')


class EducationLevelAdmin(BaseDropdownOrderAdmin):
    pass


class EnglishProficiencyAdmin(BaseDropdownOrderAdmin):
    pass


class FunctionAreaAdmin(BaseDropdownOrderAdmin):
    pass


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('country', 'name', 'alphabetic_code', )


class EmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'opt_in', 'modified_time', )
    raw_id_fields = ('user',)

    def modified_time(self, obj):
        return "{}".format(obj.modified.strftime("%B %d, %Y %H:%M:%S"))


class OrganizationMetricAdmin(admin.ModelAdmin):
    list_display = ('org', 'user', 'submission_date', 'actual_data', 'effective_date', 'total_clients',
                    'total_employees', 'local_currency', 'total_revenue', 'total_donations', 'total_expenses',
                    'total_program_expenses')
    raw_id_fields = ('user',)


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('label', 'admin', 'country', 'unclaimed_org_admin_email', 'founding_year', )
    raw_id_fields = ('admin',)


class UserExtendedProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'country_of_employment', 'role_in_org', 'hours_per_week', )
    raw_id_fields = ('user',)


class OrganizationPartnerAdmin(admin.ModelAdmin):
    list_display = ('organization', 'partner', 'start_date', 'end_date',)
    list_filter = ('organization', 'partner', 'start_date', 'end_date',)


class OrganizationMetricUpdatePromptAdmin(admin.ModelAdmin):
    list_display = ('latest_metric_submission', 'year', 'year_month', 'year_three_month', 'year_six_month',
                    'org', 'responsible_user')
    search_fields = ('org__label', 'responsible_user__username')
    raw_id_fields = ('responsible_user',)


class MetricUpdatePromptRecordAdmin(admin.ModelAdmin):
    list_display = ('prompt', 'created', 'click')
    search_fields = ('prompt__responsible_user__username', 'prompt__org__label')


class GranteeOptInAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization_partner', 'user', 'agreed', 'created_at')


class EducationAdmin(admin.ModelAdmin):
    list_display = ('id', 'linkedin_id', 'user', 'school_name', 'degree_name', 'start_month_year',
                    'end_month_year', 'description')
    raw_id_fields = ('user',)


class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('id', 'linkedin_id', 'start_date', 'end_date', 'is_current', 'title',
                    'company', 'summary')
    raw_id_fields = ('user',)


class SkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'linkedin_id', 'name')
    raw_id_fields = ('user',)


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(RoleInsideOrg, RoleInsideOrgAdmin)
admin.site.register(OrgSector, OrgSectorAdmin)
admin.site.register(OperationLevel, OperationLevelAdmin)
admin.site.register(FocusArea, FocusAreaAdmin)
admin.site.register(TotalEmployee, TotalEmployeeAdmin)
admin.site.register(PartnerNetwork, PartnerNetworkAdmin)
admin.site.register(EducationLevel, EnglishProficiencyAdmin)
admin.site.register(EnglishProficiency, EnglishProficiencyAdmin)
admin.site.register(Organization, OrganizationAdmin)
admin.site.register(UserExtendedProfile, UserExtendedProfileAdmin)
admin.site.register(EmailPreference, EmailPreferenceAdmin)
admin.site.register(FunctionArea, FunctionAreaAdmin)
admin.site.register(OrganizationPartner, OrganizationPartnerAdmin)
admin.site.register(OrganizationMetric, OrganizationMetricAdmin)
admin.site.register(OrganizationMetricUpdatePrompt, OrganizationMetricUpdatePromptAdmin)
admin.site.register(MetricUpdatePromptRecord, MetricUpdatePromptRecordAdmin)
admin.site.register(GranteeOptIn, GranteeOptInAdmin)
admin.site.register(Education, EducationAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(Skill, SkillAdmin)
