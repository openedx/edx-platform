"""
Tests for the testing Offline Mode tacks.
"""

import pytest
from unittest.mock import MagicMock, Mock, call, patch

from ddt import data, ddt, unpack
from django.conf import settings
from django.http.response import Http404

from common.djangoapps.student.tests.factories import UserFactory
from opaque_keys.edx.keys import CourseKey
from openedx.features.offline_mode.constants import OFFLINE_SUPPORTED_XBLOCKS
from openedx.features.offline_mode.tasks import (
    generate_offline_content_for_block,
    generate_offline_content_for_course,
)

from .base import CourseForOfflineTestCase


@pytest.mark.django_db
@ddt
class GenerateOfflineContentTasksTestCase(CourseForOfflineTestCase):
    """
    Test case for the testing generating offline content tacks.
    """

    def setUp(self) -> None:
        self.user = UserFactory(username=settings.OFFLINE_SERVICE_WORKER_USERNAME)
        super().setUp()

    @patch('openedx.features.offline_mode.tasks.OfflineContentGenerator')
    @patch('openedx.features.offline_mode.tasks.is_modified', return_value=True)
    def test_generate_offline_content_for_block_success(
        self,
        is_modified_mock: MagicMock,
        offline_content_generator_mock: MagicMock,
    ) -> None:
        generate_offline_content_for_block(str(self.html_block.location))

        is_modified_mock.assert_called()
        offline_content_generator_mock.assert_called_once()
        offline_content_generator_mock.return_value.generate_offline_content.assert_called_once()

    @patch('openedx.features.offline_mode.tasks.OfflineContentGenerator')
    @patch('openedx.features.offline_mode.tasks.modulestore', side_effect=Http404)
    def test_generate_offline_content_for_block_with_exception_in_offline_content_generation(
        self,
        modulestore_mock: MagicMock,
        offline_content_generator_mock: MagicMock,
    ) -> None:
        with pytest.raises(Http404):
            generate_offline_content_for_block(str(self.html_block.location))

            modulestore_mock.assert_called_once()
            offline_content_generator_mock.assert_not_called()
            offline_content_generator_mock.return_value.generate_offline_content.assert_not_called()

    @patch('openedx.features.offline_mode.tasks.generate_offline_content_for_block')
    @patch('openedx.features.offline_mode.tasks.is_modified')
    def test_generate_offline_content_for_course_supported_block_types(
        self,
        is_modified_mock: MagicMock,
        generate_offline_content_for_block_mock: MagicMock,
    ) -> None:
        is_modified_mock.return_value = True

        generate_offline_content_for_course(str(self.course.id))

        generate_offline_content_for_block_mock.assert_has_calls(
            [
                call.apply_async([str(self.html_block.location)]),
                call.apply_async([str(self.problem_block.location)]),
            ],
        )

    @patch('openedx.features.offline_mode.tasks.generate_offline_content_for_block')
    @patch('openedx.features.offline_mode.tasks.is_modified')
    @patch('openedx.features.offline_mode.tasks.modulestore')
    @data(
        (False, False),
        (True, False),
        (False, True),
    )
    @unpack
    def test_generate_offline_content_for_course_supported_block_types_for_closed_or_not_modified_xblock(
        self,
        is_modified_value_mock: bool,
        is_closed_value_mock: bool,
        modulestore_mock: MagicMock,
        is_modified_mock: MagicMock,
        generate_offline_content_for_block_mock: MagicMock,
    ) -> None:
        xblock_location_mock = 'xblock_location_mock'
        modulestore_mock.return_value.get_items.return_value = [
            Mock(location=xblock_location_mock, closed=Mock(return_value=is_closed_value_mock))
        ]
        is_modified_mock.return_value = is_modified_value_mock

        expected_call_args_for_modulestore_get_items = [
            call(CourseKey.from_string(str(self.course.id)), qualifiers={'category': offline_supported_block_type})
            for offline_supported_block_type in OFFLINE_SUPPORTED_XBLOCKS
        ]

        generate_offline_content_for_course(str(self.course.id))

        self.assertEqual(modulestore_mock.call_count, len(OFFLINE_SUPPORTED_XBLOCKS))
        self.assertListEqual(
            modulestore_mock.return_value.get_items.call_args_list, expected_call_args_for_modulestore_get_items
        )
        generate_offline_content_for_block_mock.assert_not_called()

    @patch('openedx.features.offline_mode.tasks.generate_offline_content_for_block')
    @patch('openedx.features.offline_mode.tasks.is_modified')
    @patch('openedx.features.offline_mode.tasks.modulestore')
    def test_generate_offline_content_for_course_unsupported_block_type(
        self,
        modulestore_mock: MagicMock,
        is_modified_mock: MagicMock,
        generate_offline_content_for_block_mock: MagicMock,
    ) -> None:
        is_modified_mock.return_value = True
        xblock_mock = Mock(closed=Mock(return_value=False))
        modulestore_mock.get_item.return_value = xblock_mock
        xblock_mock.block_type = 'unsupported_block_type'

        generate_offline_content_for_course(str(self.course.id))

        generate_offline_content_for_block_mock.assert_not_called()
