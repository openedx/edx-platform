"""
All views for applications app
"""
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from rest_framework.status import HTTP_400_BAD_REQUEST

from openedx.adg.lms.applications.forms import (
    BusinessLineInterestForm,
    EducationExperienceBackgroundForm,
    ExtendedUserProfileForm,
    UserApplicationForm,
    UserProfileForm
)
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from openedx.adg.lms.utils.date_utils import month_choices, year_choices

from .helpers import get_application_hub_instructions, get_course_card_information
from .models import ApplicationHub, BusinessLine, Education, MultilingualCourseGroup, UserApplication


class RedirectToLoginOrRelevantPageMixin(AccessMixin):
    """
    AccessView that allows only authenticated users with pre_conditions satisfied to access the view.
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Redirects to login page for unauthenticated users. Runs `handle_no_permission` if preconditions are not
        satisfied. Runs the view normally for authenticated user with proper conditions satisfied.
        """
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), self.get_login_url(), self.get_redirect_field_name())
        elif not self.is_precondition_satisfied():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def is_precondition_satisfied(self):
        """
        Checks if a written application is already submitted or not.

        Returns:
            bool: True if written application is not completed, False otherwise.
        """
        user_application_hub, _ = ApplicationHub.objects.get_or_create(user=self.request.user)

        return not user_application_hub.is_written_application_completed

    def handle_no_permission(self):
        """
        Redirects to application hub on get request or returns http 400 on post request.

        Returns:
            HttpResponse object.
        """
        if self.request.method == 'POST':
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
        else:
            return redirect('application_hub')


class ApplicationHubView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View to display application hub, a checklist entailing different parts of the application process, and allow
    users to submit their application.
    """

    template_name = 'adg/lms/applications/hub.html'

    def is_precondition_satisfied(self):
        """
        Checks if a user's application exists or not.

        Returns:
            Boolean, True if application exists otherwise False.
        """
        if self.request.method == 'POST':
            return False

        return ApplicationHub.objects.filter(user=self.request.user).exists()

    def handle_no_permission(self):
        """
        Redirects on test failure, `is_precondition_satisfied()` returns False.

        Returns:
            HttpResponse object.
        """
        if self.request.method == 'POST':
            return HttpResponse(status=400)
        else:
            return redirect('application_introduction')

    def get(self, request):
        """
        Send the context data i.e user_application_hub, pre_req courses, and percentage to the template for rendering.

        Returns:
            HttpResponse object.
        """
        user_application_hub = ApplicationHub.objects.get(user=self.request.user)
        pre_req_courses = business_line_courses = []
        is_any_prerequisite_started = is_locked = is_any_bu_course_started = False

        if user_application_hub.is_written_application_completed:
            pre_req_courses, is_any_prerequisite_started, is_locked = get_course_card_information(
                request.user,
                MultilingualCourseGroup.objects.get_user_program_prereq_courses(request.user)
            )

            business_line_courses, is_any_bu_course_started, _ = get_course_card_information(
                request.user,
                MultilingualCourseGroup.objects.get_user_business_line_and_common_business_line_prereq_courses(
                    request.user
                )
            )

        messages = get_application_hub_instructions(
            user_application_hub,
            is_any_prerequisite_started,
            is_any_bu_course_started
        )

        context = {
            'user_application_hub': user_application_hub,
            'pre_req_courses': pre_req_courses,
            'business_line_courses': business_line_courses,
            'is_locked': is_locked,
            'messages': messages
        }

        return render(
            request,
            self.template_name,
            context=context
        )


class ContactInformationView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View for the contact information of user application
    """

    login_url = reverse_lazy('register_user')
    template_name = 'adg/lms/applications/contact_info.html'
    user_profile_form = None
    extended_profile_form = None
    application_form = None

    def get(self, request):
        """
        Send the context data to the template for rendering.

        Returns:
            HttpResponse object.
        """
        return render(request, self.template_name, self.initialize_forms(request))

    def post(self, request):
        """
        Submit user contact information data. If successful, redirects to the experience page.

        Returns:
            HttpResponse object.
        """
        forms = self.initialize_forms(request)

        if self.is_valid():
            self.user_profile_form.save()
            self.extended_profile_form.save(request=request)
            instance = self.application_form.save(commit=False)
            instance.user = request.user
            instance.save()
            return redirect(reverse_lazy('application_education_experience'))

        return render(request, self.template_name, forms)

    def is_valid(self):
        """
        Check if the user profile, extended profile and application forms are all valid

        Returns:
            bool: True if all forms are valid, False otherwise
        """
        return (self.user_profile_form.is_valid() and self.extended_profile_form.is_valid()
                and self.application_form.is_valid())

    def initialize_forms(self, request):
        """
        Initialize the form with available data

        Returns:
            None.
        """
        application = UserApplication.objects.filter(user=request.user).first()

        if request.method == 'GET':
            self.user_profile_form = UserProfileForm(instance=request.user.profile)
            self.extended_profile_form = ExtendedUserProfileForm(initial=self.get_context_data(request))
            self.application_form = UserApplicationForm(instance=application)

        elif request.method == 'POST':
            self.user_profile_form = UserProfileForm(request.POST, instance=request.user.profile)
            self.extended_profile_form = ExtendedUserProfileForm(request.POST)
            self.application_form = UserApplicationForm(request.POST, instance=application)

        return {
            'user_profile_form': self.user_profile_form,
            'extended_profile_form': self.extended_profile_form,
            'application_form': self.application_form,
        }

    def get_context_data(self, request):
        """
        Initialize the data for extended profile form

        Returns:
            Dict.
        """
        context = {'email': request.user.email}
        extended_profile = ExtendedUserProfile.objects.filter(user=request.user).first()
        if extended_profile:
            context['saudi_national'] = extended_profile.saudi_national
            context['organization'] = extended_profile.company
            context['hear_about_omni'] = extended_profile.hear_about_omni

            if extended_profile.birth_date:
                context.update({
                    'birth_day': extended_profile.birth_date.day,
                    'birth_month': extended_profile.birth_date.month,
                    'birth_year': extended_profile.birth_date.year,
                })
        return context


class EducationAndExperienceView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View for the "My Experience" page of the written application
    """

    login_url = reverse_lazy('register_user')
    template_name = 'adg/lms/applications/education_experience.html'

    def get(self, request):
        """
        Send the context data for education and experience page.

        Returns:
            HttpResponse object.
        """
        form = EducationExperienceBackgroundForm(instance=request.user.application)
        return self.handle_rendering(request, form)

    def post(self, request):
        """
        Submit user application

        Returns:
            HttpResponse object.
        """
        user_application, _ = UserApplication.objects.get_or_create(user=request.user)
        form = EducationExperienceBackgroundForm(request.POST, instance=user_application)

        if form.is_valid():
            form.save()
        else:
            return self.handle_rendering(request, form)

        return self.handle_redirection(request, form)

    def handle_rendering(self, request, form):
        """
        Create context and render template

        Returns:
            HttpResponse object.
        """
        user_application = self.request.user.application

        context = {
            'degree_types': Education.DEGREE_TYPES,
            'month_choices': month_choices(),
            'year_choices': year_choices(),
            'user_application_id': user_application.id,
            'is_work_experience_not_applicable': user_application.is_work_experience_not_applicable,
            'is_education_experience_completed': user_application.is_education_experience_completed,
            'background_form': form,
        }

        return render(request, self.template_name, context)

    def handle_redirection(self, request, form):
        """
        Redirects to contact info page on clicking back button and to business line page
        on clicking next button

        Returns:
            HttpResponse object.
        """
        next_or_back_clicked = form.data.get('next_or_back_clicked')
        if next_or_back_clicked:
            if next_or_back_clicked == 'back':
                return redirect('application_contact')
            else:
                return redirect('application_business_line_interest')

    def is_precondition_satisfied(self):
        """
        Checks if a user's application is started but not already submitted. Furthermore,
        it checks if the user is a saudi national with an added birthdate.

        Returns:
            Boolean, True or False.
        """
        application_hub = getattr(self.request.user, 'application_hub', None)
        extended_profile = getattr(self.request.user, 'extended_profile', None)

        application_started_but_not_submitted = (
            application_hub and
            application_hub.is_written_application_started and
            not application_hub.is_written_application_completed
        )

        has_valid_profile = extended_profile and extended_profile.is_saudi_national_and_has_birthdate

        return application_started_but_not_submitted and has_valid_profile

    def handle_no_permission(self):
        """
        Redirects to application hub for get request and returns a 400 error on post request
        """
        if self.request.method == 'POST':
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
        else:
            return redirect('application_hub')


class BusinessLineInterestView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View enabling the user to select a Business Line and write their reason for interest in business.
    """

    template_name = 'adg/lms/applications/business_line_interest.html'
    login_url = reverse_lazy('register_user')

    def is_precondition_satisfied(self):
        """
        Checks that the user must have their education and experience page completed
        i.e education, work experience, and background etc should be added. Furthermore,
        the user should not have their application already submitted.

        Returns:
            Boolean, True or False.
        """
        user_application = getattr(self.request.user, 'application', None)
        application_hub = getattr(self.request.user, 'application_hub', None)

        application_started_but_not_submitted = (
            application_hub and application_hub.is_written_application_started
            and not application_hub.is_written_application_completed
        )

        education_and_experience_valid = user_application and user_application.is_education_experience_completed
        return application_started_but_not_submitted and education_and_experience_valid

    def handle_no_permission(self):
        """
        Redirects to application hub for get request and returns a 400 error on post request
        """
        if self.request.method == 'POST':
            return HttpResponse(status=HTTP_400_BAD_REQUEST)
        else:
            return redirect('application_hub')

    def get(self, request):
        """
        Send the context data for example a list of business lines and saved user_application.

        Returns:
            HttpResponse object.
        """
        form = BusinessLineInterestForm(instance=request.user.application)
        return self.handle_rendering(request, form)

    def post(self, request):
        """
        Submit user application and redirect to application hub or experience if the back button or
        submit button is clicked respectively.

        Returns:
            HttpResponse object.
        """
        user_application = request.user.application
        form = BusinessLineInterestForm(request.POST, instance=user_application)

        if form.is_valid():
            form.save()
        else:
            return self.handle_rendering(request, form)

        return self.handle_redirection(request, form, user_application)

    def handle_rendering(self, request, form):
        """
        Create context and render business line interest template

        Returns:
            HttpResponse object.
        """
        context = {
            'business_lines': BusinessLine.objects.all(),
            'application_form': form,
        }

        return render(request, self.template_name, context)

    def handle_redirection(self, request, form, application):
        """
        Redirects to education & experience page on clicking back button and to application hub page
        on clicking submit button

        Returns:
            HttpResponse object.
        """
        if form.data.get('submit_or_back_clicked') == 'back':
            return redirect('application_education_experience')
        else:
            application_hub = request.user.application_hub
            application_hub.submit_written_application_for_current_date()

            return redirect('application_hub')


class ApplicationIntroductionView(RedirectToLoginOrRelevantPageMixin, TemplateView):
    """
    View for Application introduction page
    """

    login_url = reverse_lazy('register_user')
    template_name = 'adg/lms/applications/introduction.html'

    def is_precondition_satisfied(self):
        """
        Checks if a user has visited the application hub page i.e ApplicationHub object for current user exists or not

        Returns:
            bool: True if user has visited the hub page else False
        """
        return not ApplicationHub.objects.filter(user=self.request.user).exists()

    def post(self, request):
        """
        Creates an Application Hub object for the user and redirects to Application Hub.

        Returns:
            HttpResponse object.
        """
        ApplicationHub.objects.get_or_create(user=self.request.user)

        return redirect('application_hub')
