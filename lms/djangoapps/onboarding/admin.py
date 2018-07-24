from django.contrib import admin

from lms.djangoapps.onboarding.models import (
    RoleInsideOrg,
    Currency,
    OrgSector,
    OperationLevel,
    FocusArea,
    TotalEmployee,
    PartnerNetwork,
    EducationLevel,
    EnglishProficiency,
    Organization,
    UserExtendedProfile,
    EmailPreference,
    FunctionArea,
    OrganizationPartner,
    OrganizationMetric
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
    list_display = ('user', 'opt_in', 'created', 'modified', )


class OrganizationMetricAdmin(admin.ModelAdmin):
    list_display = ('org', 'user', 'submission_date', 'actual_data', 'effective_date', 'total_clients',
                    'total_employees', 'local_currency', 'total_revenue', 'total_donations', 'total_expenses',
                    'total_program_expenses')


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('label', 'admin', 'country', 'unclaimed_org_admin_email', 'founding_year', )


class UserExtendedProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'country_of_employment', 'role_in_org', 'hours_per_week', )


class OrganizationPartnerAdmin(admin.ModelAdmin):
    list_display = ('organization', 'partner', 'start_date', 'end_date',)
    list_filter = ('organization', 'partner', 'start_date', 'end_date',)


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
