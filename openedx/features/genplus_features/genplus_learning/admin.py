from django.contrib import admin
from .models import Unit


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'course_key',
        'year_group',
    )
    search_fields = ('display_name',)
    readonly_fields = ('course_key',)
