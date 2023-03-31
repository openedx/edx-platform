"""
Test that various filters are fired for models/views in the student app.
"""
from django.http import HttpResponse
from django.test import override_settings
from common.djangoapps.util import course
from openedx_filters import PipelineStep
from openedx_filters.learning.filters import TenantAwareLinkRenderStarted
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.util.course import TenantAwareRenderNotAllowed
from openedx.core.djangolib.testing.utils import skip_unless_lms


class TestTenantAwareRenderPipelineStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, org, val_name, default):  # pylint: disable=arguments-differ
        """Pipeline step that modifies tenant aware links."""
        context = "https://tenant-aware-link"
        return {
            "context": context
        }


class TestTenantAwareFilterPrevent(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, context, org, val_name, default):  # pylint: disable=arguments-differ
        """Pipeline step that changes dashboard view response before the dashboard is rendered."""
        response = HttpResponse("This is a custom response.")
        raise TenantAwareLinkRenderStarted.PreventTenantAwarelinkRender(
            "Can't render tenant aware link.",
            response=response,
        )


@skip_unless_lms
class TenantAwareLinkFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the Tenant aware link process.

    This class guarantees that the following filters are triggered during the microsite render:

    - TenantAwareLinkRenderStarted
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.org = "test"
        self.val_name = 'LMS_ROOT_URL'
        self.default = "https://lms-base"

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.tenant_aware_link.render.started.v1": {
                "pipeline": [
                    "common.djangoapps.util.tests.test_filters.TestTenantAwareRenderPipelineStep",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_tenant_aware_filter_executed(self):
        """
        Test whether the tenant aware link filter is triggered before the user's
        render site process.

        Expected result:
            - TenantAwareLinkRenderStarted is triggered and executes TestTenantAwareRenderPipelineStep.
            - The arguments that the receiver gets are the arguments used by the filter.
        """
        course_about_url = course.get_link_for_about_page(self.course)

        expected_course_about = '{about_base_url}/courses/{course_key}/about'.format(
            about_base_url='https://tenant-aware-link',
            course_key=str(self.course.id),
        )

        self.assertEqual(expected_course_about, course_about_url)

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.learning.tenant_aware_link.render.started.v1": {
                "pipeline": [
                    "common.djangoapps.util.tests.test_filters.TestTenantAwareFilterPrevent",
                ],
                "fail_silently": False,
            },
        },
    )
    def test_tenant_aware_filter_prevent(self):
        """
        Test prevent the tenant aware link filter through a pipeline step.

        Expected result:
            - TenantAwareLinkRenderStarted is triggered and executes TestTenantAwareFilterPrevent.
            - The user can't get tenant aware links.
        """
        with self.assertRaises(TenantAwareRenderNotAllowed):
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
