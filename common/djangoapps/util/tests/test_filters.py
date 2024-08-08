"""
Test that various filters are fired for models/views in the student app.
"""
from django.http import HttpResponse
from django.test import override_settings
from common.djangoapps.util import course
from openedx_filters import PipelineStep
from openedx_filters.content_authoring.filters import LmsUrlCreationStarted
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.util.course import LmsUrlCreationNotAllowed
from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestLmsUrlCreationPipelineStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, org, val_name, default):  # pylint: disable=arguments-differ
        """Pipeline step that modifies lms url creation."""
        context = "https://lms-url-creation"
        return {
            "context": context
        }


class TestLmsUrlCreationFilterPrevent(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, org, val_name, default):  # pylint: disable=arguments-differ
        """Pipeline step that changes dashboard view response before the dashboard is rendered."""
        response = HttpResponse("This is a custom response.")
        raise LmsUrlCreationStarted.PreventLmsUrlCreationRender(
            "Can't render lms url creation.",
            response=response,
        )


@skip_unless_lms
class LmsUrlCreationStartedFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the lms url creation process.
    This class guarantees that the following filters are triggered during the microsite render:
    - LmsUrlCreationStarted
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.org = "test"
        self.val_name = 'LMS_ROOT_URL'
        self.default = "https://lms-base"

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.course_authoring.lms.url.creation.started.v1": {
                "pipeline": [
                    "common.djangoapps.util.tests.test_filters.TestLmsUrlCreationPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_lms_url_creation_filter_executed(self):
        """
        Test whether the lms url creation filter is triggered before the user's
        render site process.
        Expected result:
            - LmsUrlCreationStarted is triggered and executes TestLmsUrlCreationPipelineStep.
            - The arguments that the receiver gets are the arguments used by the filter.
        """
        course_about_url = course.get_link_for_about_page(self.course)

        expected_course_about = '{about_base_url}/courses/{course_key}/about'.format(
            about_base_url='https://lms-url-creation',
            course_key=str(self.course.id),
        )

        self.assertEqual(expected_course_about, course_about_url)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.course_authoring.lms.url.creation.started.v1": {
                "pipeline": [
                    "common.djangoapps.util.tests.test_filters.TestLmsUrlCreationFilterPrevent",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_lms_url_creation_filter_prevent(self):
        """
        Test prevent the lms url creation filter through a pipeline step.
        Expected result:
            - TenantAwareLinkRenderStarted is triggered and executes TestLmsUrlCreationFilterPrevent.
            - The user can't get lms url creation.
        """
        with self.assertRaises(LmsUrlCreationNotAllowed):
            course.get_link_for_about_page(self.course)

    @override_settings(OPEN_EDX_FILTERS_CONFIG={}, LMS_ROOT_URL="https://lms-base")
    def test_enrollment_without_filter_configuration(self):
        """
        Test usual get link for about page process, without filter's intervention.
        Expected result:
            - Returns the course sharing url, this can be one of course's social sharing url, marketing url, or
                lms course about url.
            - The get process ends successfully.
        """
        course_about_url = course.get_link_for_about_page(self.course)

        expected_course_about = '{about_base_url}/courses/{course_key}/about'.format(
            about_base_url='https://lms-base',
            course_key=str(self.course.id),
        )

        self.assertEqual(expected_course_about, course_about_url)
