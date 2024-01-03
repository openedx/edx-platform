import csv
import codecs
from django.contrib import admin
from openedx.features.genplus_features.genplus.models import *
from django.contrib import messages
from django.contrib.auth import get_user_model
from django import forms
from openedx.features.genplus_features.genplus.constants import ClassTypes
import openedx.features.genplus_features.genplus.tasks as genplus_tasks
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.template.loader import get_template
from django.shortcuts import redirect, render
from django.conf.urls import url
from openedx.features.genplus_features.genplus.constants import GenUserRoles, SchoolTypes
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

User = get_user_model()
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()
    force_change_password = forms.BooleanField(initial=True, required=False)
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    change_list_template = get_template("genplus/extended/schools_changelist.html")
    list_display = (
        'guid',
        'name',
        'type',
        'cost_center',
        'local_authority',
        'is_active',
        'external_id',
        'classes',
        'total_students',
        'logged_in_students',
        'enrolled_students'
    )
    search_fields = ('name',)
    list_filter = ('type', 'is_active', 'local_authority')
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
            force_change_password = request.POST.get('force_change_password', False)
            reader = csv.DictReader(codecs.iterdecode(csv_file, 'utf-8'))
            validated_data, error_msg = self.validate_csv(reader)
            users_created = []
            users_updated = []
            if not validated_data:
                self.message_user(request,
                                  error_msg,
                                  level=messages.ERROR)
                return redirect("..")
            reader = csv.DictReader(codecs.iterdecode(csv_file, 'utf-8'))
            for row in reader:
                try:
                    # convert dict into lower case
                    row = {k.lower().replace(" ", ""): (None if v == "" else v) for k, v in row.items()}
                    first_name = row['firstname']
                    last_name = row['secondname']
                    email = row['email']
                    password = row['password']
                    role = GenUserRoles.STUDENT
                    school, gen_class = self.get_school_and_class(row['school'],
                                                                  row['classname'],
                                                                  row['classcode'])
                    if row['role'] == GenUserRoles.TEACHING_STAFF:
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
                        try:
                            user = User.objects.get(email=email)
                            gen_user = user.gen_user
                            users_updated.append(user.email)
                        except User.DoesNotExist as e:
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
                                has_password_changed=not force_change_password
                            )
                            # activate user
                            registration.activate()
                            users_created.append(user.email)
                        if role == GenUserRoles.STUDENT:
                            gen_student = gen_user.student
                            gen_user.refresh_from_db()
                            gen_class.students.add(gen_student)
                        # process pending enrollments if any.
                        if gen_user.is_student:
                            process_pending_student_program_enrollments(gen_user)
                        elif gen_user.is_teacher:
                            process_pending_teacher_program_access(gen_user)
                    except AccountValidationError as e:
                        self.message_user(request, str(e), level=messages.ERROR)
                    except ValidationError as e:
                        self.message_user(request, str(e), level=messages.ERROR)
                except KeyError as e:
                    print(e)
                    self.message_user(request,
                                      'An Error occurred while parsing the csv. Please make sure that the csv is in the right format.',
                                      level=messages.ERROR)
            self.message_user(request,'Your csv file has been uploaded. {}'.format(str({'users_count': len(users_created),},)))
            self.message_user(request, 'New Users Created. {}'.format(str({'users_created': users_created},)))
            self.message_user(request, 'Users Updated. {}'.format(str({'users_updated': users_updated},)))
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

    @staticmethod
    def validate_csv(reader):
        try:
            for row_count, row in enumerate(reader):
                roles = [GenUserRoles.STUDENT, GenUserRoles.TEACHING_STAFF]
                non_empty_row = {k.lower().replace(" ", ""): (None if v == "" else v) for k, v in row.items()}
                role = non_empty_row['role']
                if role not in roles:
                    return False, f'Role should be {str(roles)} for row {row_count + 1}'
                first_name = non_empty_row['firstname']
                last_name = non_empty_row['secondname']
                email = non_empty_row['email']
                password = non_empty_row['password']
                school = non_empty_row['school']
                class_name = non_empty_row['classname']
                class_code = non_empty_row['classcode']
                check_list = [first_name, last_name, email, password, school]
                if role == GenUserRoles.STUDENT:
                    check_list.extend([class_code, class_name])
                if None in check_list:
                    return False, f'There are empty values on row {row_count + 1} please update that and try again.'

            return True, None
        except Exception:
            return False, 'Something wrong with the csv. Make sure to upload it in right format.'

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
