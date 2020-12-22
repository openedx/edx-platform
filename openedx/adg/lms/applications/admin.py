"""
Registering models for applications app.
"""
from django.contrib import admin
from django.contrib.auth.models import User

from .models import ApplicationHub, BusinessLine, Education, UserApplication, WorkExperience
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from student.models import UserProfile
from .forms import UserApplicationAdminForm

from django.contrib.admin import AdminSite
from .helpers import can_display_file, display_file, display_start_and_end_date
from .constants import RESUME_AND_COVER_LETTER, RESUME_ONLY, COVER_LETTER_ONLY
from django.utils.html import format_html


@admin.register(ApplicationHub)
class ApplicationHubAdmin(admin.ModelAdmin):
    """
    Django admin class for ApplicationHub
    """
    fields = (
        'user', 'is_prerequisite_courses_passed', 'is_written_application_completed', 'is_application_submitted',
        'submission_date'
    )
    list_display = (
        'id', 'user', 'is_prerequisite_courses_passed', 'is_written_application_completed', 'is_application_submitted',
        'submission_date'
    )
    raw_id_fields = ('user',)


@admin.register(UserApplication)
class UserApplicationAdmin(admin.ModelAdmin):
    """
    Django admin class for UserApplication
    """
    list_display = ('id', 'user_email', 'business_line',)
    list_filter = ('business_line',)
    raw_id_fields = ('user',)

    def user_email(self, obj):
        return obj.user.email


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    """
    Django admin class for Education
    """
    fields = (
        'name_of_school', 'degree', 'area_of_study', 'date_started_month', 'date_started_year', 'date_completed_month',
        'date_completed_year', 'is_in_progress', 'user_application',
    )
    list_display = ('id', 'name_of_school', 'degree', 'area_of_study', 'user_application',)
    list_filter = ('degree', 'area_of_study',)
    search_fields = ('name_of_school', 'degree',)


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    """
    Django admin class for WorkExperience
    """
    fields = (
        'name_of_organization', 'job_position_title', 'date_started_month', 'date_started_year', 'date_completed_month',
        'date_completed_year', 'is_current_position', 'job_responsibilities', 'user_application'
    )
    list_display = ('id', 'name_of_organization', 'job_position_title', 'user_application',)
    list_filter = ('name_of_organization', 'job_position_title',)
    search_fields = ('name_of_organization', 'job_position_title',)


@admin.register(BusinessLine)
class BusinessLineAdmin(admin.ModelAdmin):
    """
    Django admin class for BusinessLine
    """
    fields = ('title', 'logo', 'description',)
    list_display = ('id', 'title', 'logo', 'description',)
    list_filter = ('title',)
    search_fields = ('title',)


class ADGAdmin(AdminSite):
    site_header = 'Al-Dabbagh'
    site_title = site_header
    site_url = None


adg_admin_site = ADGAdmin(name='adg_admin')


class EducationInline(admin.StackedInline):
    model = Education

    fields = ('name_of_school', 'degree', 'area_of_study', 'dates')
    readonly_fields = ('name_of_school', 'degree', 'area_of_study', 'dates')

    def dates(self, obj):
        return display_start_and_end_date(obj, obj.is_in_progress)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class WorkExperienceInline(admin.StackedInline):
    model = WorkExperience

    fields = ('name_of_organization', 'job_position_title', 'dates', 'responsibilities')
    readonly_fields = ('name_of_organization', 'job_position_title', 'dates', 'responsibilities')

    def responsibilities(self, obj):
        return obj.job_responsibilities

    def dates(self, obj):
        return display_start_and_end_date(obj, obj.is_current_position)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class UserApplicationADGAdmin(admin.ModelAdmin):
    """
    Django admin class for UserApplication
    """
    list_display = ('applicant_name', 'date_received', 'status')
    list_filter = ('status', )
    list_per_page = 10

    def applicant_name(self, obj):
        return obj.user.get_full_name()

    def date_received(self, obj):
        return obj.created.strftime('%m/%d/%Y')
    date_received.short_description = 'Date Received (MM/DD/YYYY)'

    def changelist_view(self, request, extra_context=None):
        if 'status__exact' not in request.GET:
            extra_context = {'title': 'APPLICATIONS'}
        elif request.GET['status__exact'] == 'open':
            extra_context = {'title': 'OPEN APPLICATIONS'}
        elif request.GET['status__exact'] == 'accepted':
            extra_context = {'title': 'ACCEPTED APPLICATIONS'}
        elif request.GET['status__exact'] == 'waitlist':
            extra_context = {'title': 'WAITLISTED APPLICATIONS'}

        return super(UserApplicationADGAdmin, self).changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        application = UserApplication.objects.get(id=object_id)
        if request.method == 'POST':
            if 'status' in request.POST:
                new_status = request.POST.get('status')
                application.status = new_status
                if 'internal_note' in request.POST:
                    note = request.POST.get('internal_note')
                    application.internal_admin_note = note
                application.reviewed_by = request.user
                application.save()

        user_id = UserApplication.objects.get(id=object_id).user.id
        name_of_applicant = User.objects.get(id=user_id).get_full_name()

        reviewed_by = None
        review_date = None
        if application.status != 'open':
            reviewed_by = application.reviewed_by.get_full_name()
            review_date = application.modified.strftime('%B %d, %Y')

        extra_context = {
            'title': name_of_applicant,
            'adg_view': True,
            'status': application.status,
            'reviewer': reviewed_by,
            'review_date': review_date,
            'note_for_applicant': application.internal_admin_note
        }
        return super(UserApplicationADGAdmin, self).changeform_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def email(self, obj):
        return format_html('<a href="mailto:{email_address}">{email_address}</a>', email_address=obj.user.email)

    def location(self, obj):
        user_profile = UserProfile.objects.get(user=obj.user)
        return '{city}, {country}'.format(city=user_profile.city, country=user_profile.country)

    def linkedIn_profile(self, obj):
        return format_html('<a href={url}>{url}</a>', url=obj.linkedin_url)

    def is_saudi_national(self, obj):
        extended_user_profile = ExtendedUserProfile.objects.get(user=obj.user)
        if extended_user_profile.is_saudi_national:
            return 'Yes'
        return 'No'
    is_saudi_national.short_description = 'Are you a Saudi National?'

    def gender(self, obj):
        user_profile = UserProfile.objects.get(user=obj.user)
        if user_profile.gender == 'm':
            return 'Man'
        elif user_profile.gender == 'f':
            return 'Woman'
        else:
            return 'Prefer not to answer'

    def phone_number(self, obj):
        return UserProfile.objects.get(user=obj.user).phone_number

    def date_of_birth(self, obj):
        return ExtendedUserProfile.objects.get(user=obj.user).birth_date.strftime('%d %B %Y')

    def applying_to(self, obj):
        return obj.business_line

    def resume_display(self, obj):
        return display_file(obj.resume)
    resume_display.short_description = 'Resume'

    def cover_letter_display(self, obj):
        return display_file(obj.cover_letter_file)
    cover_letter_display.short_description = 'Cover Letter'

    def prerequisites(self, obj):
        html_for_score = '<p>{course_name}: <b>{course_percentage}%</b></p>'
        final_html = ''
        prereq_scores = obj.prereq_course_scores
        for prereq_score in prereq_scores:
            final_html += html_for_score.format(
                course_name=prereq_score.course_name,
                course_percentage=prereq_score.course_percentage
            )

        return format_html(final_html)

    def get_fieldsets(self, request, obj=None):
        basic_info_fields = ['email', 'location']
        if obj.linkedin_url:
            basic_info_fields.append('linkedIn_profile')

        fieldsets = [
            (None, {
                'fields': tuple(basic_info_fields)
            }),
            ('APPLICANT INFORMATION', {
                'fields': (
                        'is_saudi_national', 'gender', 'phone_number', 'date_of_birth', 'organization', 'applying_to'
                ),
            }),
        ]

        file_fields = []
        fieldset_for_files = None

        if obj.is_cover_letter_provided and obj.resume:
            fieldset_for_files = RESUME_AND_COVER_LETTER
            file_fields.append('resume')
            if obj.cover_letter_file:
                file_fields.append('cover_letter_file')
        elif obj.resume:
            fieldset_for_files = RESUME_ONLY
            file_fields.append('resume')
        elif obj.is_cover_letter_provided:
            fieldset_for_files = COVER_LETTER_ONLY
            if obj.cover_letter_file:
                file_fields.append('cover_letter_file')

        if fieldset_for_files:
            if obj.resume:
                if can_display_file(obj.resume):
                    file_fields.append('resume_display')

            if obj.cover_letter_file:
                if can_display_file(obj.cover_letter_file):
                    file_fields.append('cover_letter_display')
            elif obj.cover_letter_text:
                file_fields.append('cover_letter_text')

            fieldsets.append((fieldset_for_files, {'fields': tuple(file_fields)}))

        fieldset_for_scores = ('SCORES', {'fields': ('prerequisites', )})

        fieldsets.append(fieldset_for_scores)

        return tuple(fieldsets)

    form = UserApplicationAdminForm

    readonly_fields = (
        'email',
        'location',
        'linkedIn_profile',
        'is_saudi_national',
        'gender',
        'phone_number',
        'date_of_birth',
        'organization',
        'applying_to',
        'resume',
        'cover_letter_file',
        'cover_letter_display',
        'resume_display',
        'cover_letter_text',
        'prerequisites'
    )

    inlines = [
        EducationInline, WorkExperienceInline
    ]

    def get_formsets_with_inlines(self, request, obj=None):
        if obj.resume:
            return
        for inline in self.get_inline_instances(request, obj):
            if type(inline) == WorkExperienceInline\
                    and not WorkExperience.objects.filter(user_application=obj).exists():
                continue
            yield inline.get_formset(request, obj), inline

    def get_form(self, request, obj=None, **kwargs):
        admin_form = super(UserApplicationADGAdmin, self).get_form(request, obj, **kwargs)

        class AdminFormWithRequest(admin_form):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return admin_form(*args, **kwargs)

        return AdminFormWithRequest

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


adg_admin_site.register(UserApplication, UserApplicationADGAdmin)
