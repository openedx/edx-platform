"""
Admin registration for tags models
"""


from django.contrib import admin

from .models import TagAvailableValues, TagCategories


class TagCategoriesAdmin(admin.ModelAdmin):
    """Admin for TagCategories"""
    search_fields = ('name', 'title')
    list_display = ('id', 'name', 'title')


class TagAvailableValuesAdmin(admin.ModelAdmin):
    """Admin for TagAvailableValues"""
    list_display = ('id', 'category', 'value')


admin.site.register(TagCategories, TagCategoriesAdmin)
admin.site.register(TagAvailableValues, TagAvailableValuesAdmin)
