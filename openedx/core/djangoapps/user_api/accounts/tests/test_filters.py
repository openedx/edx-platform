"""
Test that various filters are fired for views in the certificates app.
"""
from django.http import HttpResponse
from django.test import override_settings
from django.urls import reverse
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import AccountSettingsRenderStarted
from rest_framework import status
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory


class TestRenderInvalidAccountSettings(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """
        Pipeline step that stops the course about render process.
        """
        raise AccountSettingsRenderStarted.RenderInvalidAccountSettings(
            "You can't access the account settings page.",
            account_settings_template="static_templates/server-error.html",
        )


class TestRedirectToPage(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """
        Pipeline step that redirects to dashboard before rendering the account settings page.

        When raising RedirectToPage, this filter uses a redirect_to field handled by
        the course about view that redirects to that URL.
        """
        raise AccountSettingsRenderStarted.RedirectToPage(
            "You can't access this page, redirecting to dashboard.",
            redirect_to="/courses",
        )


class TestRedirectToDefaultPage(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """
        Pipeline step that redirects to dashboard before rendering the account settings page.

        When raising RedirectToPage, this filter uses a redirect_to field handled by
        the course about view that redirects to that URL.
        """
        raise AccountSettingsRenderStarted.RedirectToPage(
            "You can't access this page, redirecting to dashboard."
        )


class TestRenderCustomResponse(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """Pipeline step that returns a custom response when rendering the account settings page."""
        response = HttpResponse("Here's the text of the web page.")
        raise AccountSettingsRenderStarted.RenderCustomResponse(
            "You can't access this page.",
            response=response,
        )


class TestAccountSettingsRender(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """Pipeline step that returns a custom response when rendering the account settings page."""
        template_name = 'static_templates/about.html'
        return {
            "context": context, "template_name": template_name,
        }


@skip_unless_lms
class TestAccountSettingsFilters(SharedModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the account settings proccess.

    This class guarantees that the following filters are triggered during the user's account settings rendering:

    - AccountSettingsRenderStarted
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.user = UserFactory.create(
            username="somestudent",
            first_name="Student",
            last_name="Person",
            email="robot@robot.org",
            is_active=True,
            password="password",
        )
        self.client.login(username=self.user.username, password="password")
        self.account_settings_url = '/account/settings'

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestAccountSettingsRender",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_account_settings_render_filter_executed(self):
        """
        Test whether the account settings filter is triggered before the user's
        account settings page is rendered.

        Expected result:
            - AccountSettingsRenderStarted is triggered and executes TestAccountSettingsRender
        """
        response = self.client.get(self.account_settings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "This page left intentionally blank. Feel free to add your own content.")

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestRenderInvalidAccountSettings",  # pylint: disable=line-too-long
                ],
                "fail_silently": False,
            },
        },
        PLATFORM_NAME="My site",
    )
    def test_account_settings_render_alternative(self):
        """
        Test whether the account settings filter is triggered before the user's
        account settings page is rendered.

        Expected result:
            - AccountSettingsRenderStarted is triggered and executes TestRenderInvalidAccountSettings  # pylint: disable=line-too-long
        """
        response = self.client.get(self.account_settings_url)

        self.assertContains(response, "There has been a 500 error on the <em>My site</em> servers")

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestRenderCustomResponse",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_account_settings_render_custom_response(self):
        """
        Test whether the account settings filter is triggered before the user's
        account settings page is rendered.

        Expected result:
            - AccountSettingsRenderStarted is triggered and executes TestRenderCustomResponse
        """
        response = self.client.get(self.account_settings_url)

        self.assertEqual(response.content, b"Here's the text of the web page.")

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestRedirectToPage",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_account_settings_redirect_to_page(self):
        """
        Test whether the account settings filter is triggered before the user's
        account settings page is rendered.

        Expected result:
            - AccountSettingsRenderStarted is triggered and executes TestRedirectToPage
        """
        response = self.client.get(self.account_settings_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual('/courses', response.url)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestRedirectToDefaultPage",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_account_settings_redirect_default(self):
        """
        Test whether the account settings filter is triggered before the user's
        account settings page is rendered.

        Expected result:
            - AccountSettingsRenderStarted is triggered and executes TestRedirectToDefaultPage
        """
        response = self.client.get(self.account_settings_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(f"{reverse('dashboard')}", response.url)

    @override_settings(OPEN_EDX_FILTERS_CONFIG={})
    def test_account_settings_render_without_filter_config(self):
        """
        Test whether the course about filter is triggered before the course about
        render without affecting its execution flow.

        Expected result:
            - AccountSettingsRenderStarted executes a noop (empty pipeline). Without any
            modification comparing it with the effects of TestAccountSettingsRender.
            - The view response is HTTP_200_OK.
        """
        response = self.client.get(self.account_settings_url)

        self.assertNotContains(response, "This page left intentionally blank. Feel free to add your own content.")
