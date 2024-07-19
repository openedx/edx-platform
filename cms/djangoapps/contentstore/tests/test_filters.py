"""
Unit tests for the asset upload endpoint.
"""
from datetime import datetime
from urllib.parse import urljoin

from pytz import UTC

from django.test import override_settings
from cms.djangoapps.contentstore import asset_storage_handlers
from opaque_keys.edx.locator import CourseLocator
from openedx_filters import PipelineStep
from xmodule.contentstore.content import StaticContent
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestPageURLRequestedPipelineStep(PipelineStep):
    """
    Utility class used when getting steps for pipeline.
    """

    def run_filter(self, url, org):  # pylint: disable=arguments-differ
        """Pipeline step that modifies lms url creation."""
        url = "https://lms-url-creation"
        org = "org"
        return {
            "url": url,
            "org": org,
        }


class LMSPageURLRequestedFiltersTest(ModuleStoreTestCase):
    """
    Tests for the Open edX Filters associated with the lms url creation process.
    This class guarantees that the following filters are triggered during the microsite render:
    - LMSPageURLRequested
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp()
        self.course = CourseFactory.create()
        self.org = "test"

    @override_settings(
        OPEN_EDX_FILTERS_CONFIG={
            "org.openedx.course_authoring.lms.page.url.requested.v1": {
                "pipeline": [
                    "common.djangoapps.util.tests.test_filters.TestPageURLRequestedPipelineStep",
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
            - LMSPageURLRequested is triggered and executes TestPageURLRequestedPipelineStep.
            - The arguments that the receiver gets are the arguments used by the filter.
        """
        upload_date = datetime(2013, 6, 1, 10, 30, tzinfo=UTC)
        content_type = 'image/jpg'
        course_key = CourseLocator('org', 'class', 'run')
        location = course_key.make_asset_key('asset', 'my_file_name.jpg')
        thumbnail_location = course_key.make_asset_key('thumbnail', 'my_file_name_thumb.jpg')

        asset_url = StaticContent.serialize_asset_key_with_slash(location)
        output = asset_storage_handlers.get_asset_json(
            "my_file",
            content_type,
            upload_date,
            location,
            thumbnail_location,
            True,
            course_key
        )

        self.assertEqual(output.get('external_url'), urljoin('https://lms-url-creation', asset_url))
