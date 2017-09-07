from django.contrib import admin

from lms.djangoapps.onboarding_survey.models import (
RoleInsideOrg,
OrgSector,
OperationLevel,
FocusArea,
TotalEmployee,
TotalVolunteer,
PartnerNetwork,
OrganizationSurvey,
OrganizationalCapacityArea,
CommunityTypeInterest,
InclusionInCommunityChoice,
PersonalGoal,
InterestsSurvey,
EducationLevel,
EnglishProficiency,
LearnerSurvey
)


admin.site.register(RoleInsideOrg)
admin.site.register(OrgSector)
admin.site.register(OperationLevel)

admin.site.register(FocusArea)
admin.site.register(TotalEmployee)
admin.site.register(TotalVolunteer)

admin.site.register(PartnerNetwork)
admin.site.register(OrganizationSurvey)
admin.site.register(OrganizationalCapacityArea)

admin.site.register(CommunityTypeInterest)
admin.site.register(InclusionInCommunityChoice)
admin.site.register(PersonalGoal)

admin.site.register(InterestsSurvey)
admin.site.register(EducationLevel)
admin.site.register(EnglishProficiency)

admin.site.register(LearnerSurvey)

