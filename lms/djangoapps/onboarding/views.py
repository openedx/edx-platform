"""HTTP endpoints for the Teams API."""

from django.shortcuts import render_to_response
from django.views.generic.base import View

from courseware import courses
from opaque_keys.edx.keys import CourseKey


class HomePageView(View):
    """
    View methods related to the home page.
    """

    def get(self, request):
        """
        Renders the home page.
        """
        context = {}
        return render_to_response("onboarding/index.html", context)


class LoginView(View):
    """
    View methods related to the login page.
    """

    def get(self, request):
        """
        Renders the login page.
        """
        context = {}
        return render_to_response("onboarding/login.html", context)


class RegisterView(View):
    """
    View methods related to the registration page.
    """

    def get(self, request):
        """
        Renders the registration page.
        """
        context = {}
        return render_to_response("onboarding/register.html", context)


class CourseDiscoveryView(View):
    """
    View methods related to the course discovery page.
    """

    def get(self, request):
        """
        Renders the course discovery page.
        """
        context = {}
        return render_to_response("onboarding/course_discovery.html", context)


class CourseAboutView(View):
    """
    View methods related to the course about page.
    """

    def get(self, request, org_string, course_string, run_string):
        """
        Renders the course about page.
        """
        course_id = "{org}/{course}/{run}".format(
            org=org_string, course=course_string, run=run_string
        )
        course_key = CourseKey.from_string(course_id)
        course = courses.get_course(course_key)
        context = {
            "course": course,
            "org_name": org_string,
            "course_name": course_string,
            "run_name": run_string,
            "course_url": "/courses/{course_key}".format(course_key=course_key),
        }
        return render_to_response("onboarding/course_about.html", context)
