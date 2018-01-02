from django.contrib import admin

from lms.djangoapps.onboarding.models import (
    RoleInsideOrg,
    OrgSector,
    OperationLevel,
    FocusArea,
    TotalEmployee,
    PartnerNetwork,
    EducationLevel,
    EnglishProficiency,
    Organization,
    UserExtendedProfile,
    FunctionArea,
)

admin.site.register(RoleInsideOrg)
admin.site.register(OrgSector)
admin.site.register(OperationLevel)
admin.site.register(FocusArea)
admin.site.register(TotalEmployee)
admin.site.register(PartnerNetwork)
admin.site.register(EducationLevel)
admin.site.register(EnglishProficiency)
admin.site.register(Organization)
admin.site.register(UserExtendedProfile)
admin.site.register(FunctionArea)
