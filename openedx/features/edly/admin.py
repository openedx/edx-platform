"""
Django Admin pages for Edly.
"""

from django.contrib import admin

from openedx.features.edly.models import (
    EdlyMultiSiteAccess,
    EdlyOrganization,
    EdlySubOrganization,
    StudentCourseProgress,
)


class EdlySubOrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for the "EdlySubOrganization" object.
    """
    search_fields = ['name', 'slug']

    list_display = [
        'edly_organization_name',
        'edly_organization_slug',
        'name',
        'slug',
        'edx_organizations_names',
        'edx_organizations_short_names',
        'is_active',
        'created',
        'modified'
    ]

    def edly_organization_name(self, obj):
        return obj.edly_organization.name

    def edly_organization_slug(self, obj):
        return obj.edly_organization.slug

    def edx_organizations_names(self, obj):
        return ', '.join(obj.edx_organizations.all().values_list('name', flat=True))

    def edx_organizations_short_names(self, obj):
        return ', '.join(obj.get_edx_organizations)


class EdlySubOrganizationInlineAdmin(admin.StackedInline):
    """
    Admin inline interface for the "EdlySubOrganization" object.
    """
    model = EdlySubOrganization
    extra = 0


class EdlyOrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for the "EdlyOrganization" object.
    """
    search_fields = ['name', 'slug']
    list_display = ['name', 'slug', 'enable_all_edly_sub_org_login', 'created', 'modified']
    inlines = [EdlySubOrganizationInlineAdmin]

class StudentCourseProgressAdmin(admin.ModelAdmin):
    """
    Admin interface for the "StudentCourseProgress" object.
    """
    list_display = ['student', 'course_id', 'completed_block', 'completion_date']
    search_fields = ['course_id', 'student__username', 'student__email']


class EdlyMultisiteAccessAdmin(admin.ModelAdmin):
    """
    Admin interface for the "EdlyMultiSiteAccess" object.
    """
    list_display = ["user", "user_email", "sub_org"]
    list_filter = ["sub_org__name"]
    search_fields = ["user__username", "user__email", "sub_org__name"]
    autocomplete_fields = ["user", "sub_org"]

    def user_email(self, obj):
        return obj.user.email


admin.site.register(StudentCourseProgress, StudentCourseProgressAdmin)
admin.site.register(EdlyOrganization, EdlyOrganizationAdmin)
admin.site.register(EdlySubOrganization, EdlySubOrganizationAdmin)
admin.site.register(EdlyMultiSiteAccess, EdlyMultisiteAccessAdmin)
