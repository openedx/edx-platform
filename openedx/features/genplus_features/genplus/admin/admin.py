from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from openedx.features.genplus_features.genplus.models import *
from openedx.features.genplus_features.genplus_learning.models import Program, UnitCompletion, ProgramEnrollment
from django.contrib import messages
import openedx.features.genplus_features.genplus.tasks as genplus_tasks
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from openedx.features.genplus_features.genplus.filters import (
    MoreThanOneClassFilter,
    DifferentActiveClassFilter,
    WithoutClassStudents,
    SchoolFilter,
)

User = get_user_model()
admin.site.unregister(User)
@admin.register(GenUser)
class GenUserAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'email',
        'role',
        'school',
        'year_of_entry',
        'registration_group',
        'social_user_exist'
    )
    search_fields = ('user__email', 'email')
    actions = ['force_change_password']

    def social_user_exist(self, obj):
        try:
            if obj.from_private_school:
                return '-'
            elif obj.user is None:
                return 'User not logged in yet.'
            else:
                return "Yes" if obj.user.social_auth.count() > 0 else "No"
        except AttributeError:
            return '-'

    def force_change_password(modeladmin, request, queryset):
        queryset.update(has_password_changed=False)
        messages.add_message(request, messages.INFO,
                             'Force password updated successfully.')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ('name',)

@admin.register(LocalAuthorityDomain)
class LocalAuthorityDomainAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(LocalAuthority)
class LocalAuthorityAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'saml_configuration_slug')
    filter_horizontal = ('domains',)

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
        'enrolled_students',
        'last_synced'
    )
    list_filter = ('school', 'is_visible', 'program', 'type')
    search_fields = ('name',)
    filter_horizontal = ('students',)
    actions = ['mark_visible', 'mark_invisible', 'sync_students']

    def sync_students(modeladmin, request, queryset):
        class_ids = queryset.values_list('id', flat=True)
        genplus_tasks.sync_student.apply_async(
            args=[list(class_ids)]
        )
        messages.add_message(request, messages.INFO,
                             'Students will be updated on background. Please refresh your page after a while.')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        db = kwargs.get('using')
        obj = kwargs.get('obj')
        object_id = request.resolver_match.kwargs.get('object_id')
        if db_field.name == 'students':
            kwargs['widget'] = FilteredSelectMultiple(
                db_field.verbose_name, is_stacked=False
            )
        else:
            return super().formfield_for_manytomany(db_field, request, **kwargs)
        if 'queryset' not in kwargs:
            queryset = None
            if object_id is not None:
                obj = Class.objects.get(pk=object_id)
            if obj.school is not None:
                queryset = Student.objects.filter(gen_user__school=obj.school)
            else:
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
        return mark_safe(
            '<a href="%s?id__in=%s">%s</a>' % (url, ','.join(map(str, students_ids)), obj.students.count()))

    def mark_visible(modeladmin, request, queryset):
        queryset.update(is_visible=True)
        messages.add_message(request, messages.INFO, 'Marked Visible')

    def mark_invisible(modeladmin, request, queryset):
        queryset.update(is_visible=False)
        messages.add_message(request, messages.INFO, 'Marked Invisible')

    def get_actions(self, request):
        def func_maker(value):
            # this function will be your update function, just mimic the traditional bulk update function
            def update_func(self, request, queryset):
                # iterating it for saving and trigger the gen_class_changed signal.
                for obj in queryset:
                    obj.program = value
                    obj.save()

            return update_func

        actions = super(ClassAdmin, self).get_actions(request)
        for value in Program.objects.all():
            func = func_maker(value)
            name = 'attach_{}'.format(value.slug.strip())
            actions['attach_{}'.format(value.slug.strip())] = (func, name,
                                                               'attach to Program: {}'.format(
                                                                   value.slug))

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


# TODO: Remove after testing the login flow
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    filter_horizontal = ('favorite_classes',)
    search_fields = ('gen_user__user__email', 'gen_user__email')
    list_filter = ('gen_user__school', 'gen_user__school__type')
    list_display = ('username', 'school')

    def username(self, obj):
        return obj.__str__()

    def school(self, obj):
        try:
            return f"{obj.gen_user.school.name} ({obj.gen_user.school.type})"
        except:
            return '-'


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    search_fields = ('gen_user__user__email', 'gen_user__email')
    list_filter = (MoreThanOneClassFilter, DifferentActiveClassFilter, 'gen_user__school',)
    list_display = ('username', 'school', 'scn', 'enrolled_classes', 'active_class', 'progress')
    autocomplete_fields = ['active_class']

    def username(self, obj):
        return obj.__str__()

    def school(self, obj):
        try:
            return f"{obj.gen_user.school.name} ({obj.gen_user.school.type})"
        except:
            return '-'

    def enrolled_classes(self, obj):
        url = reverse('admin:genplus_class_changelist')
        classes = ClassStudents.objects.filter(student=obj)
        return mark_safe('<a href="%s?id__in=%s">%s</a>' % (
            url, ','.join(map(str, classes.values_list('gen_class_id', flat=True))),
            ','.join(classes.values_list('gen_class__name', flat=True))))

    def progress(self, obj):
        if obj.gen_user.user is None:
            return 'Not logged in yet.'
        program_data = ''
        for program in Program.get_active_programs():
            units = program.units.all()
            completions = UnitCompletion.objects.filter(
                user=obj.gen_user.user,
                course_key__in=units.values_list('course', flat=True)
            )
            unit_data = ''
            for unit in units:
                try:
                    obj.gen_user.student.program_enrollments.get(program=program)
                    completion = completions.filter(user=obj.gen_user.user, course_key=unit.course.id).first()
                    progress = completion.progress if completion else 0
                    unit_html = f"""<tr>
                                  <td>{unit.display_name}</td> <td style="background-color: #eee;">{progress}%</td>
                                </tr>
                              """
                    unit_data += unit_html
                except ProgramEnrollment.DoesNotExist:
                    continue
            if unit_data:
                program_html = f"""
                                <table>
                                <tr>
                                <td><b>{program.slug}</b></td>
                                <td>
                                <table>
                                {unit_data}
                                </table>
                                </td>
                              </tr>
                            </table>
                             """
                program_data += program_html
        return mark_safe(program_data)


@admin.register(GenLog)
class GenLog(admin.ModelAdmin):
    list_filter = ('gen_log_type',)
    search_fields = ('metadata', 'description')
    list_display = ('description', 'gen_log_type', 'metadata', 'created')


@admin.register(GenError)
class GenError(admin.ModelAdmin):
    search_fields = ('email',)
    list_filter = ('school', 'gen_class', 'error_code', 'role')
    readonly_fields = ('error_code', 'name', 'email', 'role', 'school', 'gen_class', 'browser',)
    list_display = ('error_code', 'name', 'email', 'role', 'school', 'gen_class', 'browser', 'os',
                    'device', 'timestamp', 'social_user_exist')

    def social_user_exist(self, obj):
        try:
            if obj.from_private_school:
                return '-'
            elif obj.user is None:
                return 'User not logged in yet.'
            else:
                return "Yes" if obj.user.social_auth.count() > 0 else "No"
        except AttributeError:
            return '-'


@admin.register(JournalPost)
class JournalPostAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'student', 'teacher', 'title', 'description', 'journal_type')


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_filter = UserAdmin.list_filter + (
        WithoutClassStudents,
        SchoolFilter,
    )
