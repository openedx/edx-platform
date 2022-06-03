from django.contrib import admin
from openedx.features.genplus_features.genplus.models import GenUser, School


@admin.register(GenUser)
class GenUserAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'school',
        'year_of_entry',
        'registration_group'
    )
    readonly_fields = ('user', 'role', 'school', 'year_of_entry', 'registration_group')
    search_fields = ('user',)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        'guid',
        'name',
        'external_id'
    )
    readonly_fields = ('guid', 'name', 'external_id')
    search_fields = ('name',)
