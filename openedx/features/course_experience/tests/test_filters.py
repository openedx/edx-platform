"""
Test that various filters are fired for course_experience views.
"""
from django.test import override_settings
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import CourseHomeRenderStarted
from rest_framework import status

from lms.djangoapps.course_home_api.toggles import COURSE_HOME_USE_LEGACY_FRONTEND
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.course_experience.tests.views.test_course_home import TEST_WELCOME_MESSAGE, CourseHomePageTestCase


class TestStopCourseHomeRenderStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """
        Pipeline step that stops the course home render process.

        When raising PreventCourseHomeRender, this filter overrides the course home
        template name so the view renders a module-error instead.
        """
        raise CourseHomeRenderStarted.PreventCourseHomeRender(
            "You can't access the courses home page.",
            course_home_template="module-error.html",
            template_context=context,
        )


class TestRedirectCourseHomePageStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """
        Pipeline step that redirects to the course survey.

        When raising RedirectCourseHomePage, this filter uses a redirect_to field handled by
        the course home view that redirects to the URL indicated.
        """
        raise CourseHomeRenderStarted.RedirectCourseHomePage(
            "You can't access this courses home page, redirecting to the correct location.",
            redirect_to="https://course-home-elsewhere.com",
        )


class TestCourseHomeRenderStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, template_name):  # pylint: disable=arguments-differ
        """Pipeline step that removes any update messages."""
        context["update_message_fragment"] = None
        return {
            "context": context, template_name: template_name,
        }


@skip_unless_lms
class CourseHomeFiltersTest(CourseHomePageTestCase):
    """
    Tests for the Open edX Filters associated with the course home rendering process.

    This class guarantees that the following filters are triggered during the course home rendering:

    - CourseHomeRenderStarted
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course_home_url = reverse(
            'openedx.course_experience.course_home',
            kwargs={
                'course_id': self.course.id,
            }
        )

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course_home.render.started.v1": {
                "pipeline": [
                    "openedx.features.course_experience.tests.test_filters.TestCourseHomeRenderStep",
                ],
                "fail_silently": False,
            },
        },
    )
    @override_waffle_flag(COURSE_HOME_USE_LEGACY_FRONTEND, active=True)
    def test_dashboard_render_filter_executed(self):
        """
        Test whether the course home filter is triggered before the course home view
        renders.

        Expected result:
            - CourseHomeRenderStarted is triggered and executes TestCourseHomeRenderStep.
            - The course home renders without the welcome message.
        """
        self.create_course_update(TEST_WELCOME_MESSAGE)

        response = self.client.get(self.course_home_url)

        self.assertNotContains(response, TEST_WELCOME_MESSAGE, status_code=200)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course_home.render.started.v1": {
                "pipeline": [
                    "openedx.features.course_experience.tests.test_filters.TestStopCourseHomeRenderStep",
                ],
                "fail_silently": False,
            },
        },
    )
    @override_waffle_flag(COURSE_HOME_USE_LEGACY_FRONTEND, active=True)
    def test_course_home_render_invalid(self):
        """
        Test rendering an error template after catching PreventCourseHomeRender exception.

        Expected result:
            - CourseHomeRenderStarted is triggered and executes TestStopCourseHomeRenderStep.
            - The module-error template is rendered.
        """
        response = self.client.get(self.course_home_url)

        self.assertContains(response, "There has been an error on the {platform_name} servers")

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course_home.render.started.v1": {
                "pipeline": [
                    "openedx.features.course_experience.tests.test_filters.TestRedirectCourseHomePageStep",
                ],
                "fail_silently": False,
            },
        },
    )
    @override_waffle_flag(COURSE_HOME_USE_LEGACY_FRONTEND, active=True)
    def test_redirect_redirect(self):
        """
        Test redirecting to a new page after catching RedirectCourseHomePage exception.

        Expected result:
            - CourseHomeRenderStarted is triggered and executes TestCertificatePipelineStep.
            - The view response is a redirection.
        """
        response = self.client.get(self.course_home_url)

        self.assertEqual(status.HTTP_302_FOUND, response.status_code)

    @override_settings(OPEN_EDX_FILTERS_CONFIG={})
    @override_waffle_flag(COURSE_HOME_USE_LEGACY_FRONTEND, active=True)
    def test_dashboard_render_without_filter_config(self):
        """
        Test whether the course home filter is triggered before the course home
        render without affecting its execution flow.

        Expected result:
            - CourseHomeRenderStarted executes a noop (empty pipeline).
            - The webview response is HTTP_200_OK.
        """
        self.create_course_update(TEST_WELCOME_MESSAGE)

        response = self.client.get(self.course_home_url)

        self.assertContains(response, TEST_WELCOME_MESSAGE, status_code=200)
