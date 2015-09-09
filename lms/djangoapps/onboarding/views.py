"""HTTP endpoints for the Teams API."""

from django.shortcuts import render_to_response
from django.http import Http404
from django.conf import settings
from django.views.generic.base import View


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

    def get(self, request, course_key_string):
        """
        Renders the course about page.
        """
        context = {
            "course_key_string": course_key_string,
        }
        return render_to_response("onboarding/course_about.html", context)
