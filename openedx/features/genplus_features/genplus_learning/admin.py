from django.contrib import admin
from adminsortable2.admin import SortableInlineAdminMixin
from openedx.features.genplus_features.genplus_learning.models import *


@admin.register(YearGroup)
class YearGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', 'program_name',)


@admin.register(ProgramEnrollment)
class ProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'gen_class', 'program', 'status',)
    readonly_fields = ('student', 'gen_class', 'program', 'status',)
    list_filter = ('gen_class__name',)
    search_fields = ('student__gen_user__user__email', 'student__gen_user__email')


class UnitInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Unit

    def get_readonly_fields(self, request, obj):
        if isinstance(obj, Program) and not obj.is_unpublished:
            return ['course']

        return self.readonly_fields

    def has_add_permission(self, request, obj):
        if isinstance(obj, Program) and obj.is_unpublished:
            return True
        return False

    def has_delete_permission(self, request, obj):
        if isinstance(obj, Program) and obj.is_unpublished:
            return True
        return False


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    inlines = [
        UnitInline,
    ]
    search_fields = ('year_group__name',)
    list_display = (
        'year_group',
        'start_date',
        'end_date',
        'status',
    )
    readonly_fields = ('slug', 'uuid',)


admin.site.register(ProgramAccessRole)

