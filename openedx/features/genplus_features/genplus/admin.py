import csv
import codecs
from django.contrib import admin
from django.core.validators import ValidationError
from openedx.features.genplus_features.genplus.models import *
from openedx.features.genplus_features.genplus_learning.models import Program, UnitCompletion, ProgramEnrollment
from django import forms
from django.contrib import messages
from openedx.features.genplus_features.genplus.constants import ClassTypes, SchoolTypes
import openedx.features.genplus_features.genplus.tasks as genplus_tasks
from django.urls import reverse
from django.utils.text import format_lazy
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import FilteredSelectMultiple
from .filters import MoreThanOneClassFilter
from django.template.loader import get_template
from django.shortcuts import redirect, render
from django.conf.urls import url
from .constants import GenUserRoles, SchoolTypes
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from common.djangoapps.student.helpers import (
    AccountValidationError,
    do_create_account
)
from openedx.features.genplus_features.genplus.rmunify import RmUnify
from openedx.features.genplus_features.genplus_learning.utils import (
    process_pending_student_program_enrollments,
    process_pending_teacher_program_access
)
from common.djangoapps.third_party_auth.models import clean_username


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


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ('name',)


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    change_list_template = get_template("genplus/extended/schools_changelist.html")
    list_display = (
        'guid',
        'name',
        'type',
        'external_id',
        'classes',
        'total_students',
        'logged_in_students',
        'enrolled_students'
    )
    search_fields = ('name',)
    list_filter = ('type',)
    actions = ['sync_registration_group_classes', 'sync_teaching_group_classes']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url(r'import-csv/', self.import_csv),
            url(r'sync-schools/', self.sync_schools),
        ]
        return my_urls + urls

    def import_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_file"]
            reader = csv.DictReader(codecs.iterdecode(csv_file, 'utf-8'))
            for row in reader:
                try:
                    # convert dict into lower case and the empty string into None
                    non_empty_row = {k.lower().replace(" ", ""): (None if v == "" else v) for k, v in row.items()}
                    first_name = non_empty_row['firstname']
                    last_name = non_empty_row['secondname']
                    email = non_empty_row['email']
                    password = non_empty_row['password']
                    school, gen_class = self.get_school_and_class(non_empty_row['school'],
                                                                  non_empty_row['classname'],
                                                                  non_empty_row['classcode'])
                    if non_empty_row['role'] == GenUserRoles.STUDENT:
                        role = GenUserRoles.STUDENT
                    elif non_empty_row['role'] == GenUserRoles.TEACHING_STAFF:
                        role = GenUserRoles.TEACHING_STAFF
                    form = AccountCreationForm(
                        data={
                            'username': clean_username(email),
                            'email': email,
                            'password': password,
                            'name': f'{first_name} {last_name}',
                        },
                        tos_required=False,
                        do_third_party_auth=False,
                    )

                    try:
                        # register user (edx way)
                        user, profile, registration = do_create_account(form)
                        # update the user first/last names
                        user.first_name = first_name
                        user.last_name = last_name
                        user.save()
                        gen_user, created = GenUser.objects.get_or_create(
                            role=role,
                            user=user,
                            school=school,
                            email=user.email,
                        )
                        if role == GenUserRoles.STUDENT:
                            gen_student = gen_user.student
                            gen_user.refresh_from_db()
                            gen_class.students.add(gen_student)
                        # process pending enrollments if any.
                        if gen_user.is_student:
                            process_pending_student_program_enrollments(gen_user)
                        elif gen_user.is_teacher:
                            process_pending_teacher_program_access(gen_user)
                        # activate user
                        registration.activate()
                    except AccountValidationError as e:
                        self.message_user(request, str(e), level=messages.ERROR)
                    except ValidationError as e:
                        self.message_user(request, str(e), level=messages.ERROR)
                except KeyError as e:
                    print(e)
                    self.message_user(request,
                                      'An Error occurred while parsing the csv. Please make sure that the csv is in the right format.',
                                      level=messages.ERROR)
            self.message_user(request, "Your csv file has been uploaded.")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "genplus/extended/csv_form.html", payload
        )

    def sync_schools(self, request):
        rm_unify = RmUnify()
        rm_unify.fetch_schools()
        self.message_user(request, "Schools synced successfully.")
        return redirect("..")

    @staticmethod
    def get_school_and_class(school_name, class_name, class_code):
        gen_class = None
        school, created = School.objects.get_or_create(
            type=SchoolTypes.PRIVATE,
            name=school_name
        )
        if class_name and class_code:
            gen_class, created = Class.objects.get_or_create(
                name=class_name,
                group_id=class_code,
                school=school
            )
        return school, gen_class

    def classes(self, obj):
        url = reverse('admin:genplus_class_changelist')
        return mark_safe('<a href="%s?school__guid__exact=%s">%s</a>' % (url, obj.pk, obj.classes.count()))

    def total_students(self, obj):
        url = reverse('admin:genplus_student_changelist')
        student_count = Student.objects.filter(gen_user__school=obj).count()
        return mark_safe('<a href="%s?gen_user__school__guid__exact=%s">%s</a>' % (url, obj.pk, student_count))

    def logged_in_students(self, obj):
        """
        check if students is logged into the system
        in case of private schools check if last_login time is null
        in case of the rm_unify check if the user object exists or not
        """
        url = reverse('admin:genplus_student_changelist')
        students = Student.objects.filter(gen_user__school=obj, gen_user__user__last_login__isnull=False)
        if obj.type == SchoolTypes.RM_UNIFY:
            students = Student.objects.filter(gen_user__school=obj, gen_user__user__isnull=False)
        return mark_safe('<a href="%s?gen_user__school__guid__exact=%s&id__in=%s">%s</a>' % (
            url, obj.pk, ','.join(map(str, students.values_list('id', flat=True))), students.count()))

    def enrolled_students(self, obj):
        """
        check enrolled students by checking if program enrollments against that users exist or not
        """
        url = reverse('admin:genplus_student_changelist')
        students = Student.objects.filter(gen_user__school=obj, gen_user__user__isnull=False,
                                          program_enrollments__isnull=False)
        return mark_safe('<a href="%s?gen_user__school__guid__exact=%s&id__in=%s">%s</a>' % (
            url, obj.pk, ','.join(map(str, students.values_list('id', flat=True))), students.count()))

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
            name = 'attach_{}'.format(value.year_group.name.strip())
            actions['attach_{}'.format(value.year_group.name.strip())] = (func, name,
                                                                          'attach to Program: {}'.format(
                                                                              value.year_group.name))

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
    list_filter = (MoreThanOneClassFilter, 'gen_user__school',)
    list_display = ('username', 'school', 'enrolled_classes', 'progress')

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
        program_data = {}
        for program in Program.get_active_programs():
            units = program.units.all()
            completions = UnitCompletion.objects.filter(
                user=obj.gen_user.user,
                course_key__in=units.values_list('course', flat=True)
            )
            unit_data = {}
            for unit in units:
                try:
                    obj.gen_user.student.program_enrollments.get(program=program)
                    completion = completions.filter(user=obj.gen_user.user, course_key=unit.course.id).first()
                    progress = completion.progress if completion else 0
                    unit_data[unit.display_name] = f"{int(progress)}%"
                except ProgramEnrollment.DoesNotExist:
                    continue
            if unit_data:
                program_data[program.year_group.name] = unit_data
            else:
                program_data[program.year_group.name] = "Not enrolled yet"
        return str(program_data)
