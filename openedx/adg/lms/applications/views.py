"""
All views for applications app
"""
from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from openedx.adg.common.course_meta.models import CourseMeta
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .helpers import send_application_submission_confirmation_email
from .models import ApplicationHub


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
