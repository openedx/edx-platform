"""
Registering models for applications app.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from openedx.adg.lms.constants import SAUDI_NATIONAL_PROMPT

from .constants import (
    APPLYING_TO,
    COVER_LETTER_FILE,
    COVER_LETTER_FILE_DISPLAY,
    COVER_LETTER_ONLY,
    COVER_LETTER_TEXT,
    DATE_OF_BIRTH,
    EMAIL,
    GENDER,
    IS_SAUDI_NATIONAL,
    LINKED_IN_PROFILE,
    LOCATION,
    ORGANIZATION,
    PHONE_NUMBER,
    PREREQUISITES,
    RESUME,
    RESUME_AND_COVER_LETTER,
    RESUME_DISPLAY,
    RESUME_ONLY,
    SCORES
)
from .forms import UserApplicationAdminForm
from .helpers import (
    get_duration,
    get_embedded_view_html,
    get_extra_context_for_application_review_page,
    is_displayable_on_browser
)
from .models import ApplicationHub, BusinessLine, Education, UserApplication, WorkExperience


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
    """
    Subclass AdminSite to create a new admin site for ADG admins where they can review applications.
    """

    site_header = _('Al-Dabbagh')
    site_title = site_header
    site_url = None


adg_admin_site = ADGAdmin(name='adg_admin')


class ApplicationReviewInline(admin.StackedInline):
    """
    Abstract inline for inlines to be rendered in application review page.

    Restrict inline deletion and addition rights from ADG admin.
    """

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class EducationInline(ApplicationReviewInline):
    """
    InlineModelAdmin for Education model
    """

    model = Education

    fields = ('name_of_school', 'degree', 'area_of_study', 'dates')
    readonly_fields = fields

    def dates(self, obj):
        return get_duration(obj, obj.is_in_progress)


class WorkExperienceInline(ApplicationReviewInline):
    """
    InlineModelAdmin for WorkExperience model
    """

    model = WorkExperience

    fields = ('name_of_organization', 'job_position_title', 'dates', 'responsibilities')
    readonly_fields = fields

    def dates(self, obj):
        return get_duration(obj, obj.is_current_position)

    def responsibilities(self, obj):
        return obj.job_responsibilities


class UserApplicationADGAdmin(admin.ModelAdmin):
    """
    Django admin class for UserApplication
    """

    form = UserApplicationAdminForm

    readonly_fields = (
        EMAIL,
        LOCATION,
        LINKED_IN_PROFILE,
        IS_SAUDI_NATIONAL,
        GENDER,
        PHONE_NUMBER,
        DATE_OF_BIRTH,
        ORGANIZATION,
        APPLYING_TO,
        RESUME,
        COVER_LETTER_FILE,
        COVER_LETTER_FILE_DISPLAY,
        RESUME_DISPLAY,
        COVER_LETTER_TEXT,
        PREREQUISITES
    )

    inlines = [
        EducationInline, WorkExperienceInline
    ]

    list_display = ('applicant_name', 'date_received', 'status')
    list_filter = ('status', )
    list_per_page = 10

    def get_queryset(self, request):
        """
        Override `get_queryset` method of BaseModelAdmin to show ADG admin only those applications which have been
        submitted successfully.
        """
        return UserApplication.submitted_applications.all()

    def applicant_name(self, obj):
        return obj.user.profile.name

    def date_received(self, obj):
        return obj.user.application_hub.submission_date.strftime('%m/%d/%Y')
    date_received.short_description = _('Date Received (MM/DD/YYYY)')

    def changelist_view(self, request, extra_context=None):
        """
        Extend change list view of application listing page for ADG admin.

        Extension is done to customize heading of the application listing page, depending on the application status
        filter that the admin has selected.
        """
        application_status_map = {
            UserApplication.OPEN: _('OPEN APPLICATIONS'),
            UserApplication.ACCEPTED: _('ACCEPTED APPLICATIONS'),
            UserApplication.WAITLIST: _('WAITLISTED APPLICATIONS')
        }

        extra_context = {'title': _('APPLICATIONS')}
        if 'status__exact' in request.GET:
            extra_context['title'] = application_status_map[request.GET['status__exact']]

        return super(UserApplicationADGAdmin, self).changelist_view(request, extra_context=extra_context)

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """
        Extend change form view of application review page for ADG admin.

        Extension is required to handle conditionally storing review information and to provide extra context to the
        review form.

        Arguments:
            request(WSGIRequest): Http Request
            object_id (str): ID of application under review
            form_url (str): URL of the application review form
            extra_context (NoneType): Extra context to be passed to the application review form template

        Returns:
            TemplateResponse: Template response to render application review form
        """
        if request.method == 'POST' and 'status' in request.POST:
            self._save_application_review_info(object_id, request)

        application = self._get_user_application(object_id)
        extra_context = get_extra_context_for_application_review_page(application)

        return super(UserApplicationADGAdmin, self).changeform_view(
            request, object_id, form_url, extra_context=extra_context
        )

    def _save_application_review_info(self, application_id, request):
        """
        Save application review information.

        Save new status of application (waitlist/accepted) and optional internal note.

        Arguments:
            application_id (str): ID of application under review
            request (WSGIRequest): Post request containing application review information
        """
        application = self._get_user_application(application_id)

        new_status = request.POST.get('status')
        application.status = new_status

        if 'internal_note' in request.POST:
            note = request.POST.get('internal_note')
            application.internal_admin_note = note

        application.reviewed_by = request.user

        application.save()

    def _get_user_application(self, application_id):
        return UserApplication.objects.get(id=application_id)

    def email(self, obj):
        return format_html('<a href="mailto:{email_address}">{email_address}</a>', email_address=obj.user.email)

    def location(self, obj):
        user_profile = obj.user.profile
        return '{city}, {country}'.format(city=user_profile.city, country=user_profile.country)

    def linked_in_profile(self, obj):
        return format_html('<a href={url}>{url}</a>', url=obj.linkedin_url)
    linked_in_profile.short_description = _('LinkedIn Profile')

    def is_saudi_national(self, obj):
        extended_user_profile = obj.user.extended_profile
        return extended_user_profile.is_saudi_national
    is_saudi_national.short_description = SAUDI_NATIONAL_PROMPT

    def gender(self, obj):
        """
        Return gender of applicant
        """
        user_profile = obj.user.profile
        if user_profile.gender == 'm':
            return _('Man')
        elif user_profile.gender == 'f':
            return _('Woman')
        else:
            return _('Prefer not to answer')

    def phone_number(self, obj):
        return obj.user.profile.phone_number

    def date_of_birth(self, obj):
        extended_user_profile = obj.user.extended_profile
        return extended_user_profile.birth_date.strftime('%d %B %Y')

    def applying_to(self, obj):
        return obj.business_line

    def resume_display(self, obj):
        return get_embedded_view_html(obj.resume)
    resume_display.short_description = _('Resume')

    def cover_letter_file_display(self, obj):
        return get_embedded_view_html(obj.cover_letter_file)
    cover_letter_file_display.short_description = _('Cover Letter')

    def prerequisites(self, obj):
        """
        Get scores of the applicant in prerequisite courses of the franchise program.

        Arguments:
            obj (UserApplication): Application under review

        Returns:
            SafeText: HTML containing course name of all prereq courses and applicant's respective scores in those
            courses
        """
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
        """
        Override `get_fieldsets` method of BaseModelAdmin.

        Override is needed to group application under different sections and dynamically set fields to be rendered.

        Arguments:
            request (WSGIRequest): HTTP request accessing application review page
            obj (UserApplication): Application under review

        Returns:
            tuple: Tuple of fieldsets
        """
        fieldsets = []

        preliminary_info_fieldset = self._get_preliminary_info_fieldset(obj)
        fieldsets.append(preliminary_info_fieldset)

        applicant_info_fieldset = self._get_applicant_info_fieldset()
        fieldsets.append(applicant_info_fieldset)

        if obj.cover_letter_or_resume:
            fieldset_for_resume_cover_letter = self._get_fieldset_for_resume_cover_letter(obj)
            fieldsets.append(fieldset_for_resume_cover_letter)

        fieldset_for_scores = self._get_fieldset_for_scores()
        fieldsets.append(fieldset_for_scores)

        return tuple(fieldsets)

    def _get_preliminary_info_fieldset(self, application):
        """
        Get fieldset for preliminary applicant information.

        Arguments:
            application (UserApplication): Application under review

        Returns:
            tuple: Fieldset containing email, location and optionally linkedIn profile
        """
        fieldset_title = ''

        preliminary_info_fields = [EMAIL, LOCATION]
        if application.linkedin_url:
            preliminary_info_fields.append(LINKED_IN_PROFILE)

        fieldset = (fieldset_title, {'fields': tuple(preliminary_info_fields)})

        return fieldset

    def _get_applicant_info_fieldset(self):
        """
        Get fieldset for applicant information.

        Returns:
            tuple: Fieldset containing applicant's nationality info, gender, contact number, date of birth, organization
                    and the business line they are applying to.
        """
        fieldset_title = _('APPLICANT INFORMATION')
        applicant_info_fields = (IS_SAUDI_NATIONAL, GENDER, PHONE_NUMBER, DATE_OF_BIRTH, ORGANIZATION, APPLYING_TO)
        fieldset = (fieldset_title, {'fields': applicant_info_fields})

        return fieldset

    def _get_fieldset_for_resume_cover_letter(self, application):
        """
        Prepare and return fieldset for resume and cover letter provided with application.

        Arguments:
            application (UserApplication): Application under review

        Returns:
            tuple: Fieldset containing both fieldset title and a child tuple for fields.

                Title for fieldset varies based on the provided data. If the applicant has provided:

                    both cover letter and resume, title returned is 'RESUME & COVER LETTER',
                    resume only, title returned is 'RESUME'
                    cover letter only, either as an attachment or in text, title returned is 'COVER LETTER'

                Fields returned as part of the fieldset also vary depending on the data that the applicant has provided
        """
        resume_cover_letter_file_fields = []

        if application.cover_letter_and_resume:
            fieldset_title = RESUME_AND_COVER_LETTER
            resume_cover_letter_file_fields.append(RESUME)
            if application.cover_letter_file:
                resume_cover_letter_file_fields.append(COVER_LETTER_FILE)
        elif application.resume:
            fieldset_title = RESUME_ONLY
            resume_cover_letter_file_fields.append(RESUME)
        else:
            fieldset_title = COVER_LETTER_ONLY
            if application.cover_letter_file:
                resume_cover_letter_file_fields.append(COVER_LETTER_FILE)

        resume_cover_letter_display_fields = self._get_resume_cover_letter_display_fields(application)

        resume_cover_letter_fields = resume_cover_letter_file_fields + resume_cover_letter_display_fields
        fieldset = (fieldset_title, {'fields': tuple(resume_cover_letter_fields)})

        return fieldset

    def _get_resume_cover_letter_display_fields(self, application):
        """
        Get display fields, if applicable, for resume and/or cover letter

        Arguments:
            application (UserApplication): Application under review

        Returns:
            list: Display fields
        """
        resume_cover_letter_display_fields = []

        if application.resume:
            if is_displayable_on_browser(application.resume):
                resume_cover_letter_display_fields.append(RESUME_DISPLAY)

        if application.cover_letter_file:
            if is_displayable_on_browser(application.cover_letter_file):
                resume_cover_letter_display_fields.append(COVER_LETTER_FILE_DISPLAY)
        elif application.cover_letter:
            resume_cover_letter_display_fields.append(COVER_LETTER_TEXT)

        return resume_cover_letter_display_fields

    def _get_fieldset_for_scores(self):
        """
        Get fieldset for scores of applicant in prerequisite courses.

        Returns:
            tuple: Fieldset
        """
        fieldset = (SCORES, {'fields': (PREREQUISITES, )})

        return fieldset

    def get_formsets_with_inlines(self, request, obj=None):
        """
        Override method `get_formsets_with_inlines` of ModelAdmin.

        Override is needed to ensure that if the applicant has attached a resume, the education and work experience
        inlines should not be rendered. If resume is not attached with application, EducationInline should be rendered
        while WorkExperienceInline should be optionally rendered depending on whether the user has entered any.

        Arguments:
            request (WSGIRequest): HTTP request accessing application review page
            obj (UserApplication): Application under review

        Returns:
            Formsets with inlines
        """
        if obj.resume:
            return

        for inline in self.get_inline_instances(request, obj):
            if isinstance(inline, WorkExperienceInline) and obj.has_no_work_experience:
                continue

            yield inline.get_formset(request, obj), inline

    def get_form(self, request, obj=None, change=False, **kwargs):
        """
        Extend method `get_form` of ModelAdmin.

        Extension is needed to attach request object with the admin form. The request object is needed in the `clean`
        method that is extended in `UserApplicationAdminForm`

        Arguments:
            request (WSGIRequest): HTTP request accessing application review page
            obj (UserApplication): Application under review
            change (bool): Type of form

        Returns:
            AdminFormWithRequest: Application review form for admin with request object added as a keyword argument
        """
        admin_form = super(UserApplicationADGAdmin, self).get_form(request, obj, **kwargs)

        class AdminFormWithRequest(admin_form):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                return admin_form(*args, **kwargs)

        return AdminFormWithRequest

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


adg_admin_site.register(UserApplication, UserApplicationADGAdmin)
