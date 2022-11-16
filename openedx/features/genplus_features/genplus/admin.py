from django.contrib import admin
from openedx.features.genplus_features.genplus.models import *
from openedx.features.genplus_features.genplus_learning.models import Program
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from django.contrib import messages
from openedx.features.genplus_features.genplus.constants import ClassTypes
import openedx.features.genplus_features.genplus.tasks as genplus_tasks
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from .filters import MoreThanOneClassFilter

@admin.register(GenUser)
class GenUserAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'school',
        'year_of_entry',
        'registration_group'
    )
    search_fields = ('user',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        'guid',
        'name',
        'type',
        'external_id',
        'classes',
        'students'
    )
    search_fields = ('name',)
    list_filter = ('type', )
    actions = ['sync_registration_group_classes', 'sync_teaching_group_classes']

    def classes(self, obj):
        url = reverse('admin:genplus_class_changelist')
        return mark_safe('<a href="%s?school__guid__exact=%s">%s</a>' % (url, obj.pk, obj.classes.count()))

    def students(self, obj):
        url = reverse('admin:genplus_student_changelist')
        student_count = Student.objects.filter(gen_user__school=obj).count()
        return mark_safe('<a href="%s?gen_user__school__guid__exact=%s">%s</a>' % (url, obj.pk, student_count))

    def sync_registration_group_classes(modeladmin, request, queryset):
        schools_ids = queryset.values_list('guid', flat=True)
        genplus_tasks.sync_schools.apply_async(
            args=[ClassTypes.REGISTRATION_GROUP, list(schools_ids)]
        )
        messages.add_message(request, messages.INFO,
                             'Classes will be updated on background. Please refresh your page after a while.')

    def sync_teaching_group_classes(modeladmin, request, queryset):
        schools_ids = queryset.values_list('guid', flat=True)
        genplus_tasks.sync_schools.apply_async(
            args=[ClassTypes.TEACHING_GROUP, list(schools_ids)]
        )
        messages.add_message(request, messages.INFO,
                             'Classes will be updated on background. Please refresh your page after a while.')


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    filter_horizontal = ('skills',)
    search_fields = ('name',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_visible',
        'program',
        'type',
        'enrolled_students'
    )
    list_filter = ('school', 'is_visible', 'program', 'type')
    search_fields = ('name',)
    filter_horizontal = ('students',)
    actions = ['mark_visible', 'sync_students']

    def sync_students(modeladmin, request, queryset):
        class_ids = queryset.values_list('id', flat=True)
        genplus_tasks.sync_student.apply_async(
            args=[list(class_ids)]
        )
        messages.add_message(request, messages.INFO,
                             'Students will be updated on background. Please refresh your page after a while.')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        db = kwargs.get('using')

        if db_field.name == 'students':
            kwargs['widget'] = FilteredSelectMultiple(
                db_field.verbose_name, is_stacked=False
            )
        else:
            return super().formfield_for_manytomany(db_field, request, **kwargs)
        if 'queryset' not in kwargs:
            queryset = Student.objects.all()
            if queryset is not None:
                kwargs['queryset'] = queryset
        form_field = db_field.formfield(**kwargs)
        msg = 'Hold down “Control”, or “Command” on a Mac, to select more than one.'
        help_text = form_field.help_text
        form_field.help_text = (
            format_lazy('{} {}', help_text, msg) if help_text else msg
        )
        return form_field

    def enrolled_students(self, obj):
        url = reverse('admin:genplus_student_changelist')
        students_ids = obj.students.values_list('id', flat=True)
        return mark_safe('<a href="%s?id__in=%s">%s</a>' % (url, ','.join(map(str, students_ids)), obj.students.count()))

    def mark_visible(modeladmin, request, queryset):
        queryset.update(is_visible=True)
        messages.add_message(request, messages.INFO, 'Marked Visible')

    def get_actions(self, request):
        def func_maker(value):
            # this function will be your update function, just mimic the traditional bulk update function
            def update_func(self, request, queryset):
                queryset.update(program=value)
            return update_func
        actions = super(ClassAdmin, self).get_actions(request)
        for value in Program.objects.all():
            func = func_maker(value)
            name = 'attach_{}'.format(value.year_group.name.strip())
            actions['attach_{}'.format(value.year_group.name.strip())] = (func, name,
                                                                          'attach to Program: {}'.format(value.year_group.name))

        return actions

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return self.readonly_fields + ('program',)

        if obj and obj.program:
            return self.readonly_fields + ('program',)

        return self.readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "program":
            kwargs["queryset"] = Program.get_active_programs()
        return super(ClassAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(TeacherClass)
class TeacherClassAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'gen_class', 'is_favorite')


# TODO: Remove after testing the login flow
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    filter_horizontal = ('classes',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_filter = (MoreThanOneClassFilter, 'gen_user__school', )
    list_display = ('username', 'school', 'enrolled_classes', )

    def username(self, obj):
        return obj.__str__()

    def school(self, obj):
        try:
            return obj.gen_user.school.name
        except:
            return '-'

    def enrolled_classes(self, obj):
        url = reverse('admin:genplus_class_changelist')
        classes = ClassStudents.objects.filter(student=obj)
        return mark_safe('<a href="%s?id__in=%s">%s</a>' % (
            url, ','.join(map(str, classes.values_list('gen_class_id', flat=True))), classes.count()))


admin.site.register(JournalPost)
admin.site.register(Activity)
admin.site.register(ClassStudents)
admin.site.register(TempUser)
