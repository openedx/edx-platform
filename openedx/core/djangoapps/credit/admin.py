"""
Django admin page for credit eligibility
"""
from ratelimitbackend import admin

from openedx.core.djangoapps.credit.models import (
    CreditConfig, CreditCourse, CreditProvider, CreditEligibility, CreditRequest, CreditRequirement,
    CreditRequirementStatus
)


class CreditCourseAdmin(admin.ModelAdmin):
    """Admin for credit courses. """
    list_display = ('course_key', 'enabled',)
    list_filter = ('enabled',)
    search_fields = ('course_key',)

    class Meta(object):
        model = CreditCourse


class CreditProviderAdmin(admin.ModelAdmin):
    """Admin for credit providers. """
    list_display = ('provider_id', 'display_name', 'active',)
    list_filter = ('active',)
    search_fields = ('provider_id', 'display_name')

    class Meta(object):
        model = CreditProvider


class CreditEligibilityAdmin(admin.ModelAdmin):
    """Admin for credit eligibility. """
    list_display = ('course', 'username', 'deadline')
    search_fields = ('username', 'course__course_key')

    class Meta(object):
        model = CreditEligibility


class CreditRequestAdmin(admin.ModelAdmin):
    """Admin for credit requests. """
    list_display = ('provider', 'course', 'status', 'username')
    list_filter = ('provider', 'status',)
    readonly_fields = ('uuid',)
    search_fields = ('uuid', 'username', 'course__course_key', 'provider__provider_id')

    class Meta(object):
        model = CreditRequest


class CreditRequirementAdmin(admin.ModelAdmin):
    """ Admin for CreditRequirement. """
    list_display = ('course', 'namespace', 'name', 'display_name', 'active',)
    list_filter = ('active', 'namespace',)
    search_fields = ('course__course_key', 'namespace', 'name',)

    class Meta(object):
        model = CreditRequirement


class CreditRequirementStatusAdmin(admin.ModelAdmin):
    """ Admin for CreditRequirementStatus. """
    list_display = ('username', 'requirement', 'status',)
    search_fields = ('username', 'requirement__course__course_key',)

    class Meta(object):
        model = CreditRequirementStatus


admin.site.register(CreditCourse, CreditCourseAdmin)
admin.site.register(CreditProvider, CreditProviderAdmin)
admin.site.register(CreditEligibility, CreditEligibilityAdmin)
admin.site.register(CreditRequest, CreditRequestAdmin)
admin.site.register(CreditConfig)
admin.site.register(CreditRequirement, CreditRequirementAdmin)
admin.site.register(CreditRequirementStatus, CreditRequirementStatusAdmin)
