from django.contrib import admin
from .models import *


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'course_key',
        'usage_key',
        'is_locked',
    )
    readonly_fields = ('course_key', 'usage_key',)


@admin.register(YearGroup)
class YearGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', 'program_name',)


@admin.register(ClassEnrollment)
class ClassEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('gen_class', 'program')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "program":
            kwargs["queryset"] = Program.get_current_programs()
        return super(ClassEnrollmentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


# TODO: Remove this after testing
@admin.register(ProgramEnrollment)
class ProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('gen_user', 'from_class', 'program', 'status')
    readonly_fields = ('gen_user', 'from_class', 'program')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "program":
            kwargs["queryset"] = Program.get_current_programs()
        return super(ProgramEnrollmentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ProgramUnitEnrollment)
class ProgramUnitEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('program_enrollment', 'unit')
    readonly_fields = ('program_enrollment', 'unit', 'course_enrollment')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    search_fields = ('year_group__name',)
    list_display = (
        'year_group',
        'start_date',
        'end_date',
        'is_current',
    )
    filter_horizontal = ('units',)
