""" Tagging app admin """
from django.contrib import admin

from .models import ContentTaxonomy


class ContentTaxonomyOrgAdmin(admin.TabularInline):
    model = ContentTaxonomy.org_owners.through


class ContentTaxonomyAdmin(admin.ModelAdmin):
    """
    Admin form for the content taxonomy table.
    """

    inlines = (ContentTaxonomyOrgAdmin,)


admin.site.register(ContentTaxonomy, ContentTaxonomyAdmin)
