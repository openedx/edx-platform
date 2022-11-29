import csv
import codecs
from django.contrib import admin
from openedx.features.genplus_features.genplus.models import *
from openedx.features.genplus_features.genplus_learning.models import Program
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
from .constants import GenUserRoles
from django.contrib.auth.models import User


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
        'students'
    )
    search_fields = ('name',)
    list_filter = ('type', )
    actions = ['sync_registration_group_classes', 'sync_teaching_group_classes']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            url(r'import-csv/', self.import_csv),
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
                    username = non_empty_row['username'] if non_empty_row['username'] else email
                    password = non_empty_row['password']
                    role = GenUserRoles.STUDENT if non_empty_row['role'] == GenUserRoles.STUDENT else GenUserRoles.TEACHING_STAFF
                    school, gen_class = self.get_school_and_class(non_empty_row['school'],
                                                                  non_empty_row['classname'],
                                                                  non_empty_row['classcode'])
                    user, created = User.objects.get_or_create(
                                username=username,
                                email=email,
                                first_name=first_name,
                                last_name=last_name,
                        )
                    user.set_password(password)
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
                except KeyError as e:
                    print(e)
                    self.message_user(request, 'An Error occurred while parsing the csv', level=messages.ERROR)
            self.message_user(request, "Your csv file has been imported")
            return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "genplus/extended/csv_form.html", payload
        )

    @staticmethod
    def get_school_and_class(school_name, class_name, class_code):
        school, created = School.objects.get_or_create(
            type=SchoolTypes.PRIVATE,
            name=school_name
        )
        gen_class, created = Class.objects.get_or_create(
            name=class_name,
            group_id=class_code,
            school=school
        )
        return school, gen_class



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
