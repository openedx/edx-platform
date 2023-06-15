from django.contrib import admin
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating, SkillAssessmentResponse


class BaseModelAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site):
        self.model = model
        super().__init__(model, admin_site)
        self.list_display = [field.name for field in self.model._meta.get_fields()]


@admin.register(UserResponse)
class UserResponseAdmin(BaseModelAdmin):
    pass


@admin.register(UserRating)
class UserRatingAdmin(BaseModelAdmin):
    pass


@admin.register(SkillAssessmentResponse)
class SkillAssessmentResponseAdmin(BaseModelAdmin):
    pass
