"""
Test that various filters are fired for models/views in the student app.
"""
from django.test import override_settings
from common.djangoapps.util import course
from openedx_filters import PipelineStep
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestPageURLRequestedPipelineStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, url, org):  # pylint: disable=arguments-differ
        """Pipeline step that modifies lms url requested."""
        url = "https://lms-url-creation"
        org = "org"
        return {
            "url": url,
            "org": org,
        }


@skip_unless_lms
class CourseAboutPageURLRequestedFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the lms url creation process.
    This class guarantees that the following filters are triggered during the microsite render:
    - CourseAboutPageURLRequested
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.course_about.page.url.requested.v1": {
                "pipeline": [
                    "common.djangoapps.util.tests.test_filters.TestPageURLRequestedPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_course_about_page_url_requested_filter_executed(self):
        """
        Test whether the lms url requested filter is triggered before the user's
        render site process.
        Expected result:
            - CourseAboutPageURLRequested is triggered and executes TestPageURLRequestedPipelineStep.
            - The arguments that the receiver gets are the arguments used by the filter.
        """
        course_about_url = course.get_link_for_about_page(self.course)

        self.assertEqual("https://lms-url-creation", course_about_url)

    @override_settings(OPEN_EDX_FILTERS_CONFIG={}, LMS_ROOT_URL="https://lms-base")
    def test_course_about_page_url_requested_without_filter_configuration(self):
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
