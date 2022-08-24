from django.contrib import admin
from .models import *


@admin.register(ClassLesson)
class ClassLessonAdmin(admin.ModelAdmin):
    list_display = (
        'class_unit',
        'usage_key',
        'is_locked',
    )
    readonly_fields = ('class_unit', 'usage_key', 'course_key',)


@admin.register(YearGroup)
class YearGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', 'program_name',)


# TODO: Remove this after testing
@admin.register(ProgramEnrollment)
class ProgramEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'gen_class', 'program', 'status',)
    readonly_fields = ('student', 'gen_class', 'program',)


@admin.register(ProgramUnitEnrollment)
class ProgramUnitEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('program_enrollment', 'course',)
    readonly_fields = ('program_enrollment', 'course', 'course_enrollment',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    search_fields = ('year_group__name',)
    list_display = (
        'year_group',
        'start_date',
        'end_date',
        'is_current',
    )
    readonly_fields = ('uuid', 'slug',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('course', 'program',)

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.program:
            return self.readonly_fields + ('course', 'program',)
        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "program":
            kwargs["queryset"] = Program.get_current_programs()
        return super(UnitAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ClassUnit)
class ClassUnitAdmin(admin.ModelAdmin):
    list_display = ('gen_class', 'unit',)
    readonly_fields = ('gen_class', 'unit',)


admin.site.register(UnitCompletion)
admin.site.register(UnitBlockCompletion)
