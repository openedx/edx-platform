"""
Django admin page for credit eligibility
"""
from ratelimitbackend import admin
from openedx.core.djangoapps.credit.models import (
    CreditCourse, CreditProvider, CreditEligibility, CreditRequest
)


class CreditCourseAdmin(admin.ModelAdmin):
    """Admin for credit courses. """
    search_fields = ("course_key",)


class CreditProviderAdmin(admin.ModelAdmin):
    """Admin for credit providers. """
    search_fields = ("provider_id", "display_name")


class CreditEligibilityAdmin(admin.ModelAdmin):
    """Admin for credit eligibility. """
    search_fields = ("username", "course__course_key")


class CreditRequestAdmin(admin.ModelAdmin):
    """Admin for credit requests. """
    search_fields = ("uuid", "username", "course__course_key", "provider__provider_id")
    readonly_fields = ("uuid",)


admin.site.register(CreditCourse, CreditCourseAdmin)
admin.site.register(CreditProvider, CreditProviderAdmin)
admin.site.register(CreditEligibility, CreditEligibilityAdmin)
admin.site.register(CreditRequest, CreditRequestAdmin)
