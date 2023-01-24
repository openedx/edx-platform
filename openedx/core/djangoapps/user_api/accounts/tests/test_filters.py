"""
Test that various filters are fired for views in the certificates app.
"""
from django.http import HttpResponse
from django.test import override_settings
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import AccountSettingsRenderStarted
from rest_framework import status
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


class TestRedirectToPageStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context):  # pylint: disable=arguments-differ
        """Pipeline step that redirects to dashboard before rendering the account settings page."""

        raise AccountSettingsRenderStarted.RedirectToPage(
            "You can't access this page, redirecting to dashboard.",
            redirect_to="/dashboard",
        )


class TestRenderCustomResponse(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context):  # pylint: disable=arguments-differ
        """Pipeline step that returns a custom response when rendering the account settings page."""
        response = HttpResponse("Here's the text of the web page.")
        raise AccountSettingsRenderStarted.RenderCustomResponse(
            "You can't access this page.",
            response=response,
        )

class TestAccountSettingsRenderPipelineStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context):  # pylint: disable=arguments-differ
        """Pipeline step that returns a custom response when rendering the account settings page."""
        context += {
            'test': 'test',
        }
        return context

class TestAccountSettingsFilters(SharedModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the account settings proccess.

    This class guarantees that the following filters are triggered during the user's account settings rendering:

    - AccountSettingsRenderStarted
    """

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestAccountSettingsRenderPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_account_settings_render_pipeline_step(self):
        """
        Test whether the account settings filter is triggered before the user's
        account settings page is rendered.

        Expected result:
            - AccountSettingsRenderStarted is triggered and executes TestAccountSettingsRenderPipelineStep
        """
        response = self.client.get('/account/settings')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.context['test'], 'test')


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
        response = self.client.get('/account/settings')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b"Here's the text of the web page.")


    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.student.settings.render.started.v1": {
                "pipeline": [
                    "openedx.core.djangoapps.user_api.accounts.tests.test_filters.TestRedirectToPageStep",
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
            - AccountSettingsRenderStarted is triggered and executes TestRedirectToPageStep
        """
        response = self.client.get('/account/settings')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/dashboard')
