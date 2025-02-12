"""
Tests for the testing utility functions for managing assets and files for Offline Mode.
"""

import os

from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

from botocore.exceptions import ClientError
from django.conf import settings
from path import Path
from pytz import UTC

from openedx.features.offline_mode.assets_management import (
    block_storage_path,
    clean_outdated_xblock_files,
    create_subdirectories_for_asset,
    get_offline_block_content_path,
    get_static_file_path,
    is_modified,
    save_asset_file,
    save_mathjax_to_xblock_assets,
)
from openedx.features.offline_mode.constants import MATHJAX_CDN_URL, MATHJAX_STATIC_PATH
from xmodule.modulestore.exceptions import ItemNotFoundError


class AssetsManagementTestCase(TestCase):
    """
    Test case for the testing utility functions for managing assets and files.
    """

    def test_get_static_file_path(self) -> None:
        relative_path_mock = 'relative_path_mock'
        expected_result = Path(f'{settings.STATIC_ROOT}/{relative_path_mock}')

        result = get_static_file_path(relative_path_mock)

        self.assertEqual(result, expected_result)

    @patch('openedx.features.offline_mode.assets_management.open')
    @patch('openedx.features.offline_mode.assets_management.create_subdirectories_for_asset')
    @patch('openedx.features.offline_mode.assets_management.os.path.join')
    @patch('openedx.features.offline_mode.assets_management.AssetManager.find')
    @patch('openedx.features.offline_mode.assets_management.StaticContent.get_asset_key_from_path')
    def test_save_asset_file_if_filename_contains_slash(
        self,
        get_asset_key_from_path_mock: MagicMock,
        asset_manager_find_mock: MagicMock,
        os_path_join_mock: MagicMock,
        create_subdirectories_for_asset_mock: MagicMock,
        context_manager_mock: MagicMock,
    ) -> None:
        temp_dir_mock = 'temp_dir_mock'
        xblock_mock = Mock()
        path_mock = 'path_mock'
        filename_mock = 'assets/filename_mock'

        save_asset_file(temp_dir_mock, xblock_mock, path_mock, filename_mock)

        get_asset_key_from_path_mock.assert_called_once_with(
            xblock_mock.location.course_key, filename_mock.split('/')[-1]
        )
        asset_manager_find_mock.assert_called_once_with(get_asset_key_from_path_mock.return_value)
        os_path_join_mock.assert_called_once_with(temp_dir_mock, filename_mock)
        create_subdirectories_for_asset_mock.assert_called_once_with(os_path_join_mock.return_value)
        context_manager_mock.assert_called_once_with(os_path_join_mock.return_value, 'wb')
        context_manager_mock.return_value.__enter__.return_value.write.assert_called_once_with(
            asset_manager_find_mock.return_value.data
        )

    @patch('openedx.features.offline_mode.assets_management.open')
    @patch('openedx.features.offline_mode.assets_management.create_subdirectories_for_asset')
    @patch('openedx.features.offline_mode.assets_management.os.path.join')
    @patch('openedx.features.offline_mode.assets_management.read_static_file')
    @patch('openedx.features.offline_mode.assets_management.get_static_file_path')
    def test_save_asset_file_no_slash_in_filename(
        self,
        get_static_file_path_mock: MagicMock,
        read_static_file_mock: MagicMock,
        os_path_join_mock: MagicMock,
        create_subdirectories_for_asset_mock: MagicMock,
        context_manager_mock: MagicMock,
    ) -> None:
        temp_dir_mock = 'temp_dir_mock'
        xblock_mock = Mock()
        path_mock = 'path_mock'
        filename_mock = 'filename_mock'

        save_asset_file(temp_dir_mock, xblock_mock, path_mock, filename_mock)

        get_static_file_path_mock.assert_called_once_with(filename_mock)
        read_static_file_mock.assert_called_once_with(get_static_file_path_mock.return_value)
        os_path_join_mock.assert_called_once_with(
            temp_dir_mock, 'assets', filename_mock,
        )
        create_subdirectories_for_asset_mock.assert_called_once_with(os_path_join_mock.return_value)
        context_manager_mock.assert_called_once_with(os_path_join_mock.return_value, 'wb')
        context_manager_mock.return_value.__enter__.return_value.write.assert_called_once_with(
            read_static_file_mock.return_value
        )

    @patch('openedx.features.offline_mode.assets_management.log.warning')
    @patch(
        'openedx.features.offline_mode.assets_management.get_static_file_path', side_effect=ItemNotFoundError
    )
    def test_save_asset_file_can_not_find(
        self,
        get_static_file_path_mock: MagicMock,
        log_warning_mock: MagicMock,
    ) -> None:
        temp_dir_mock = 'temp_dir_mock'
        xblock_mock = Mock()
        path_mock = 'path_mock'
        filename_mock = 'filename_mock'

        save_asset_file(temp_dir_mock, xblock_mock, path_mock, filename_mock)

        get_static_file_path_mock.assert_called_once_with(filename_mock)
        log_warning_mock.assert_called_once_with(
            f'Asset not found: {filename_mock}, during offline content generation.'
        )

    @patch('openedx.features.offline_mode.assets_management.os')
    def test_create_subdirectories_for_asset_subdirectories_does_not_exist(self, os_mock: MagicMock) -> None:
        file_path_mock = 'file/path/mock/'
        os_mock.path.exists.return_value = False

        expected_os_path_join_call_args_list = [
            call('/', 'file'),
            call(os_mock.path.join.return_value, 'path'),
            call(os_mock.path.join.return_value, 'mock'),
        ]
        expected_os_mock_mkdir_call_args_list = [
            call(os_mock.path.join.return_value),
            call(os_mock.path.join.return_value),
            call(os_mock.path.join.return_value),
        ]

        create_subdirectories_for_asset(file_path_mock)

        self.assertListEqual(os_mock.path.join.call_args_list, expected_os_path_join_call_args_list)
        self.assertListEqual(os_mock.mkdir.call_args_list, expected_os_mock_mkdir_call_args_list)

    @patch('openedx.features.offline_mode.assets_management.os')
    def test_create_subdirectories_for_asset_subdirectories_exist(self, os_mock: MagicMock) -> None:
        file_path_mock = 'file/path/mock/'

        expected_os_path_join_call_args_list = [
            call('/', 'file'),
            call(os_mock.path.join.return_value, 'path'),
            call(os_mock.path.join.return_value, 'mock'),
        ]

        create_subdirectories_for_asset(file_path_mock)

        self.assertListEqual(os_mock.path.join.call_args_list, expected_os_path_join_call_args_list)
        os_mock.mkdir.assert_not_called()

    @patch('openedx.features.offline_mode.assets_management.log')
    @patch('openedx.features.offline_mode.assets_management.default_storage')
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    def test_clean_outdated_xblock_files_successful(
        self,
        block_storage_path_mock: MagicMock,
        default_storage_mock: MagicMock,
        logger_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        default_storage_mock.exists.return_value = True
        expected_offline_zip_path = os.path.join(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip'
        )

        clean_outdated_xblock_files(xblock_mock)

        block_storage_path_mock.assert_called_once_with(xblock_mock)
        default_storage_mock.exists.assert_called_once_with(expected_offline_zip_path)
        default_storage_mock.delete.assert_called_once_with(expected_offline_zip_path)
        logger_mock.info.assert_called_once_with(f'Successfully deleted the file: {expected_offline_zip_path}')

    @patch('openedx.features.offline_mode.assets_management.log')
    @patch('openedx.features.offline_mode.assets_management.default_storage')
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    def test_clean_outdated_xblock_files_does_not_exist(
        self,
        block_storage_path_mock: MagicMock,
        default_storage_mock: MagicMock,
        logger_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        default_storage_mock.exists.return_value = False
        expected_offline_zip_path = os.path.join(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip'
        )

        clean_outdated_xblock_files(xblock_mock)

        block_storage_path_mock.assert_called_once_with(xblock_mock)
        default_storage_mock.exists.assert_called_once_with(expected_offline_zip_path)
        default_storage_mock.delete.assert_not_called()
        logger_mock.info.assert_not_called()

    @patch('openedx.features.offline_mode.assets_management.log.error')
    @patch('openedx.features.offline_mode.assets_management.default_storage.exists')
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    def test_remove_old_files_client_error(
        self,
        block_storage_path_mock: MagicMock,
        default_storage_exists_mock: MagicMock,
        log_error_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        default_storage_exists_mock.side_effect = ClientError(
            operation_name='InvalidKeyPair.Duplicate', error_response={
                'Error': {'Code': 'Duplicate', 'Message': 'Invalid File Path'}
            }
        )
        expected_error_message = (
            'An error occurred (Duplicate) when calling the InvalidKeyPair.Duplicate operation: Invalid File Path'
        )

        clean_outdated_xblock_files(xblock_mock)
        block_storage_path_mock.assert_called_once_with(xblock_mock)
        log_error_mock.assert_called_once_with(
            f'Error occurred while deleting the files or directory: {expected_error_message}'
        )

    @patch('openedx.features.offline_mode.assets_management.default_storage.exists')
    @patch('openedx.features.offline_mode.assets_management.os.path.join', return_value='offline_zip_path_mock')
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    def test_get_offline_block_content_path_offline_content_exists(
        self,
        block_storage_path_mock: MagicMock,
        os_path_join_mock: MagicMock,
        default_storage_exists_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()

        result = get_offline_block_content_path(xblock_mock)

        block_storage_path_mock.assert_called_once_with(usage_key=xblock_mock.location)
        os_path_join_mock.assert_called_once_with(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip'
        )
        default_storage_exists_mock.assert_called_once_with(os_path_join_mock.return_value)
        self.assertEqual(result, 'offline_zip_path_mock')

    @patch('openedx.features.offline_mode.assets_management.default_storage.exists', return_value=False)
    @patch('openedx.features.offline_mode.assets_management.os.path.join', return_value='offline_zip_path_mock')
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    def test_get_offline_block_content_path_does_not_exist(
        self,
        block_storage_path_mock: MagicMock,
        os_path_join_mock: MagicMock,
        default_storage_exists_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()

        result = get_offline_block_content_path(xblock_mock)

        block_storage_path_mock.assert_called_once_with(usage_key=xblock_mock.location)
        os_path_join_mock.assert_called_once_with(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip'
        )
        default_storage_exists_mock.assert_called_once_with(os_path_join_mock.return_value)
        self.assertEqual(result, None)

    def test_block_storage_path_exists(self) -> None:
        xblock_mock = Mock(location=Mock(course_key='course_key_mock'))

        result = block_storage_path(xblock_mock)

        self.assertEqual(result, 'offline_content/course_key_mock/')

    def test_block_storage_path_does_not_exists(self) -> None:
        result = block_storage_path()

        self.assertEqual(result, '')

    @patch(
        'openedx.features.offline_mode.assets_management.default_storage.get_modified_time',
        return_value=datetime(2024, 6, 12, tzinfo=UTC)
    )
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    @patch('openedx.features.offline_mode.assets_management.os.path.join')
    def test_is_modified_true(
        self,
        os_path_join_mock: MagicMock,
        block_storage_path_mock: MagicMock,
        get_created_time_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock(published_on=datetime(2024, 6, 13, tzinfo=UTC))

        result = is_modified(xblock_mock)

        os_path_join_mock.assert_called_once_with(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip')
        get_created_time_mock.assert_called_once_with(os_path_join_mock.return_value)
        self.assertEqual(result, True)

    @patch(
        'openedx.features.offline_mode.assets_management.default_storage.get_modified_time',
        return_value=datetime(2024, 6, 12, tzinfo=UTC)
    )
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    @patch('openedx.features.offline_mode.assets_management.os.path.join')
    def test_is_modified_false(
        self,
        os_path_join_mock: MagicMock,
        block_storage_path_mock: MagicMock,
        get_created_time_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock(published_on=datetime(2024, 6, 1, tzinfo=UTC))

        result = is_modified(xblock_mock)

        os_path_join_mock.assert_called_once_with(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip')
        get_created_time_mock.assert_called_once_with(os_path_join_mock.return_value)
        self.assertEqual(result, False)

    @patch(
        'openedx.features.offline_mode.assets_management.default_storage.get_modified_time',
        side_effect=OSError
    )
    @patch('openedx.features.offline_mode.assets_management.block_storage_path')
    @patch('openedx.features.offline_mode.assets_management.os.path.join')
    def test_is_modified_os_error(
        self,
        os_path_join_mock: MagicMock,
        block_storage_path_mock: MagicMock,
        get_created_time_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()

        result = is_modified(xblock_mock)

        os_path_join_mock.assert_called_once_with(
            block_storage_path_mock.return_value, f'{xblock_mock.location.block_id}.zip')
        get_created_time_mock.assert_called_once_with(os_path_join_mock.return_value)
        self.assertEqual(result, True)

    @patch('openedx.features.offline_mode.assets_management.log.info')
    @patch('openedx.features.offline_mode.assets_management.open')
    @patch('openedx.features.offline_mode.assets_management.requests.get')
    @patch('openedx.features.offline_mode.assets_management.os')
    def test_save_mathjax_to_xblock_assets_successfully(
        self,
        os_mock: MagicMock,
        requests_get_mock: MagicMock,
        context_manager_mock: MagicMock,
        logger_mock: MagicMock,
    ) -> None:
        temp_dir_mock = 'temp_dir_mock'
        os_mock.path.exists.return_value = False

        save_mathjax_to_xblock_assets(temp_dir_mock)

        os_mock.path.join.assert_called_once_with(temp_dir_mock, MATHJAX_STATIC_PATH)
        os_mock.path.exists.assert_called_once_with(os_mock.path.join.return_value)
        requests_get_mock.assert_called_once_with(MATHJAX_CDN_URL)
        context_manager_mock.assert_called_once_with(os_mock.path.join.return_value, 'wb')
        context_manager_mock.return_value.__enter__.return_value.write.assert_called_once_with(
            requests_get_mock.return_value.content
        )
        logger_mock.assert_called_once_with(f'Successfully saved MathJax to {os_mock.path.join.return_value}')

    @patch('openedx.features.offline_mode.assets_management.log.info')
    @patch('openedx.features.offline_mode.assets_management.open')
    @patch('openedx.features.offline_mode.assets_management.requests.get')
    @patch('openedx.features.offline_mode.assets_management.os')
    def test_save_mathjax_to_xblock_assets_already_exists(
        self,
        os_mock: MagicMock,
        requests_get_mock: MagicMock,
        context_manager_mock: MagicMock,
        logger_mock: MagicMock,
    ) -> None:
        temp_dir_mock = 'temp_dir_mock'

        save_mathjax_to_xblock_assets(temp_dir_mock)

        os_mock.path.join.assert_called_once_with(temp_dir_mock, MATHJAX_STATIC_PATH)
        os_mock.path.exists.assert_called_once_with(os_mock.path.join.return_value)
        requests_get_mock.assert_not_called()
        context_manager_mock.assert_not_called()
        logger_mock.assert_not_called()
