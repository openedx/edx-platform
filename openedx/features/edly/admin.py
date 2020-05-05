"""
Django Admin pages for Edly.
"""

from django.contrib import admin

from openedx.features.edly.models import EdlyOrganization, EdlySubOrganization


class EdlySubOrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for the EdlySubOrganization object.
    """
    search_fields = ['name', 'slug']

    list_display = [
        'edly_organization_name',
        'edly_organization_slug',
        'name',
        'slug',
        'edx_organization_name',
        'edx_organization_short_name',
        'created',
        'modified'
    ]

    def edly_organization_name(self, obj):
        return obj.edly_organization.name

    def edly_organization_slug(self, obj):
        return obj.edly_organization.slug

    def edx_organization_name(self, obj):
        return obj.edx_organization.name

    def edx_organization_short_name(self, obj):
        return obj.edx_organization.short_name


class EdlySubOrganizationInlineAdmin(admin.StackedInline):
    """
    Admin inline interface for the EdlySubOrganization object.
    """
    model = EdlySubOrganization
    extra = 0


class EdlyOrganizationAdmin(admin.ModelAdmin):
    """
    Admin interface for the EdlyOrganization object.
    """
    list_display = ['name', 'slug', 'created', 'modified']
    inlines = [EdlySubOrganizationInlineAdmin]


admin.site.register(EdlyOrganization, EdlyOrganizationAdmin)
admin.site.register(EdlySubOrganization, EdlySubOrganizationAdmin)
