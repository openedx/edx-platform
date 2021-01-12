"""
All views for applications app
"""
from pathlib import Path

from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView
from rest_framework.status import HTTP_400_BAD_REQUEST

from openedx.adg.common.course_meta.models import CourseMeta
from openedx.adg.lms.applications.forms import ExtendedUserProfileForm, UserApplicationForm, UserProfileForm
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .helpers import send_application_submission_confirmation_email
from .models import ApplicationHub, BusinessLine, UserApplication


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


class ApplicationHubView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View to display application hub, a checklist entailing different parts of the application process, and allow
    users to submit their application.
    """

    template_name = 'adg/lms/applications/hub.html'

    def is_precondition_satisfied(self):
        """
        Checks if a user's application is already submitted or not.

        Returns:
            Boolean, True or False.
        """
        user_application_hub, _ = ApplicationHub.objects.get_or_create(user=self.request.user)

        if self.request.method == 'POST':
            return user_application_hub.are_application_pre_reqs_completed()
        else:
            return not user_application_hub.is_application_submitted

    def handle_no_permission(self):
        """
        Redirects on test failure, `is_precondition_satisfied()` returns False.

        Returns:
            HttpResponse object.
        """
        if self.request.method == 'POST':
            return HttpResponse(status=400)
        else:
            return redirect('application_success')

    def get(self, request):
        """
        Send the context data i.e user_application_hub, pre_req courses, and percentage to the template for rendering.

        Returns:
            HttpResponse object.
        """
        user_application_hub, _ = ApplicationHub.objects.get_or_create(user=self.request.user)
        pre_req_course_ids = CourseMeta.open_pre_req_courses.all()
        pre_req_courses = [CourseOverview.get_from_id(course_id) for course_id in pre_req_course_ids]

        return render(
            request,
            self.template_name,
            context={'user_application_hub': user_application_hub, 'pre_req_courses': pre_req_courses}
        )

    def post(self, request):
        """
        Submit user application, send mandrill email according to the Application Confirmation Email format. In the
        end, it redirects to the application success page.

        Returns:
            HttpResponse object.
        """
        if not request.user.application_hub.is_application_submitted:
            request.user.application_hub.submit_application_for_current_date()
            send_application_submission_confirmation_email(request.user.email)
        return redirect('application_success')


class ApplicationSuccessView(RedirectToLoginOrRelevantPageMixin, TemplateView):
    """
    View entailing successfully submitted application status of a user.
    """

    template_name = 'adg/lms/applications/success.html'

    def is_precondition_satisfied(self):
        """
        Checks if a user's application is already submitted or not.

        Returns:
            Boolean, True or False.
        """
        try:
            return self.request.user.application_hub.is_application_submitted
        except ApplicationHub.DoesNotExist:
            return False

    def handle_no_permission(self):
        """
        Redirects on test failure, `test_func()` returns False.

        Returns:
            HttpResponse object.
        """
        return HttpResponse(status=400)

    def get_context_data(self, **kwargs):
        """
        Send the application submission date for the authenticated user in the context dictionary.

        Returns:
            dict object.
        """
        context = super(ApplicationSuccessView, self).get_context_data(**kwargs)
        context['submission_date'] = self.request.user.application_hub.submission_date
        return context


class ContactInformationView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View for the contact information of user application
    """

    login_url = '/register'
    template_name = 'adg/lms/applications/contact_info.html'
    user_profile_form = None
    extended_profile_form = None
    application_form = None

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
        If resume is added, then experience page is skipped and redirect to application cover letter page.

        Returns:
            HttpResponse object.
        """
        forms = self.initialize_forms(request)
        if self.is_valid():

            self.user_profile_form.save()
            self.extended_profile_form.save(request=request)
            instance = self.application_form.save(commit=False)
            instance.user = request.user
            if self.application_form.data.get('delete-file') == 'Yes':
                instance.resume.delete()
            instance.save()

            if self.application_form.cleaned_data.get('resume'):
                return redirect(reverse_lazy('application_cover_letter'))
            return redirect(reverse_lazy('application_experience'))
        return render(request, self.template_name, forms)

    def is_valid(self):
        """
        Send the context data to the template for rendering.

        Returns:
            Boolean object.
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
            self.application_form = UserApplicationForm(request.POST, request.FILES, instance=application)

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

            if extended_profile.birth_date:
                context.update({
                    'birth_day': extended_profile.birth_date.day,
                    'birth_month': extended_profile.birth_date.month,
                    'birth_year': extended_profile.birth_date.year,
                })
        return context


class CoverLetterView(RedirectToLoginOrRelevantPageMixin, View):
    """
    View enabling the user to select a Business Line and upload or write a cover letter.
    """

    template_name = 'adg/lms/applications/cover_letter.html'
    login_url = '/register'

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
            return HttpResponse(status=400)
        else:
            return redirect('application_hub')

    def get(self, request):
        """
        Send the context data for example a list of business lines and saved user_application.
        Returns:
            HttpResponse object.
        """
        business_lines = BusinessLine.objects.all()
        file_name = None

        try:
            registration_business_line = request.user.extended_profile.company
        except ExtendedUserProfile.DoesNotExist:
            registration_business_line = None

        try:
            user_application = request.user.application
            if user_application.cover_letter_file:
                file_name = Path(user_application.cover_letter_file.name).name
        except UserApplication.DoesNotExist:
            user_application = None

        context = {
            'business_lines': business_lines,
            'user_application': user_application,
            'registration_business_line': registration_business_line,
            'csrf_token': get_token(request),
            'filename': file_name
        }

        return render(request, self.template_name, context)

    def post(self, request):
        """
        Submit user application and redirect to application hub or experience depending upon button click.
        Returns:
            HttpResponse object.
        """
        user_application, _ = UserApplication.objects.get_or_create(user=request.user)

        if 'business_line' in request.POST and request.POST['business_line']:
            business_line = BusinessLine.objects.get(id=request.POST['business_line'])
            user_application.business_line = business_line

        if 'text-coverletter' in request.POST:
            if request.POST['text-coverletter']:
                cover_letter_text = request.POST['text-coverletter']
                user_application.cover_letter = cover_letter_text
            else:
                user_application.cover_letter = ''

            user_application.cover_letter_file = None

        elif 'add-coverletter' in request.FILES:
            cover_letter_file = request.FILES['add-coverletter']
            user_application.cover_letter = ''
            user_application.cover_letter_file = cover_letter_file

        if 'business_line' in request.POST or 'text-coverletter' in request.POST or 'add-coverletter' in request.FILES:
            user_application.save()

        if request.POST['next'] == 'back':
            return redirect('application_experience')
        else:
            application_hub = request.user.application_hub
            application_hub.set_is_written_application_completed()
            return redirect('application_hub')
