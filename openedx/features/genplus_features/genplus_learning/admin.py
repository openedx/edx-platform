from django.contrib import admin, messages
from adminsortable2.admin import SortableInlineAdminMixin
from openedx.features.genplus_features.genplus_learning.models import *


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'is_current')
    actions = ['mark_as_current', ]

    def mark_as_current(modeladmin, request, queryset):
        if queryset.count() > 1:
            messages.add_message(request, messages.ERROR, 'You cannot mark more than one academic year as current.')
        else:
            # marking the other academic year as non-active
            AcademicYear.objects.filter(is_current=True).update(is_current=False)
            queryset.update(is_current=True)
            messages.add_message(request, messages.SUCCESS, 'Marked as current.')

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
        'slug',
        'academic_year',
        'start_date',
        'end_date',
        'status',
        'staff_browsable',
        'student_browsable',
    )
    readonly_fields = ('slug', 'uuid',)


@admin.register(ClassLesson)
class ClassLessonAdmin(admin.ModelAdmin):
    list_display = ('class_unit', 'course_key', 'usage_key')

admin.site.register(ProgramAccessRole)

