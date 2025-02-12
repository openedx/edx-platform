"""
Tests for the testing Offline Mode storage management.
"""

import os
import shutil
from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

from django.http.response import Http404

from openedx.features.offline_mode.constants import MATHJAX_STATIC_PATH
from openedx.features.offline_mode.storage_management import OfflineContentGenerator
from openedx.features.offline_mode.tests.base import CourseForOfflineTestCase


class OfflineContentGeneratorTestCase(TestCase):
    """
    Test case for the testing Offline Mode utils.
    """
    @patch('openedx.features.offline_mode.storage_management.XBlockRenderer')
    def test_render_block_html_data_successful(self, xblock_renderer_mock: MagicMock) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'

        result = OfflineContentGenerator(xblock_mock, html_data_mock).render_block_html_data()

        xblock_renderer_mock.assert_called_once_with(str(xblock_mock.location))
        xblock_renderer_mock.return_value.render_xblock_from_lms.assert_called_once_with()
        self.assertEqual(result, xblock_renderer_mock.return_value.render_xblock_from_lms.return_value)

    @patch('openedx.features.offline_mode.storage_management.XBlockRenderer')
    def test_render_block_html_data_successful_no_html_data(self, xblock_renderer_mock: MagicMock) -> None:
        xblock_mock = Mock()
        expected_xblock_renderer_args_list = [call(str(xblock_mock.location)), call(str(xblock_mock.location))]

        result = OfflineContentGenerator(xblock_mock).render_block_html_data()

        self.assertListEqual(xblock_renderer_mock.call_args_list, expected_xblock_renderer_args_list)
        self.assertListEqual(
            xblock_renderer_mock.return_value.render_xblock_from_lms.call_args_list, [call(), call()]
        )
        self.assertEqual(result, xblock_renderer_mock.return_value.render_xblock_from_lms.return_value)

    @patch('openedx.features.offline_mode.storage_management.log.error')
    @patch('openedx.features.offline_mode.storage_management.XBlockRenderer', side_effect=Http404)
    def test_render_block_html_data_http404(
        self,
        xblock_renderer_mock: MagicMock,
        logger_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'

        with self.assertRaises(Http404):
            OfflineContentGenerator(xblock_mock, html_data_mock).render_block_html_data()

        xblock_renderer_mock.assert_called_once_with(str(xblock_mock.location))
        logger_mock.assert_called_once_with(
            f'Block {str(xblock_mock.location)} cannot be fetched from course'
            f' {xblock_mock.location.course_key} during offline content generation.'
        )

    @patch('openedx.features.offline_mode.storage_management.shutil.rmtree')
    @patch('openedx.features.offline_mode.storage_management.OfflineContentGenerator.create_zip_file')
    @patch('openedx.features.offline_mode.storage_management.OfflineContentGenerator.save_xblock_html')
    @patch('openedx.features.offline_mode.storage_management.mkdtemp')
    @patch('openedx.features.offline_mode.storage_management.clean_outdated_xblock_files')
    @patch('openedx.features.offline_mode.storage_management.block_storage_path')
    def test_generate_offline_content_for_modified_xblock(
        self,
        block_storage_path_mock: MagicMock,
        clean_outdated_xblock_files_mock: MagicMock,
        mkdtemp_mock: MagicMock,
        save_xblock_html_mock: MagicMock,
        create_zip_file_mock: MagicMock,
        shutil_rmtree_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'

        OfflineContentGenerator(xblock_mock, html_data_mock).generate_offline_content()

        block_storage_path_mock.assert_called_once_with(xblock_mock)
        clean_outdated_xblock_files_mock.assert_called_once_with(xblock_mock)
        mkdtemp_mock.assert_called_once_with()
        save_xblock_html_mock.assert_called_once_with(mkdtemp_mock.return_value)
        create_zip_file_mock.assert_called_once_with(
            mkdtemp_mock.return_value,
            block_storage_path_mock.return_value,
            f'{xblock_mock.location.block_id}.zip'
        )
        shutil_rmtree_mock.assert_called_once_with(mkdtemp_mock.return_value, ignore_errors=True)

    @patch('openedx.features.offline_mode.storage_management.os.path.join')
    @patch('openedx.features.offline_mode.storage_management.open')
    @patch('openedx.features.offline_mode.storage_management.HtmlManipulator')
    def test_save_xblock_html(
        self,
        html_manipulator_mock: MagicMock,
        context_manager_mock: MagicMock,
        os_path_join_mock: MagicMock,
    ) -> None:
        tmp_dir_mock = Mock()
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'

        OfflineContentGenerator(xblock_mock, html_data_mock).save_xblock_html(tmp_dir_mock)

        html_manipulator_mock.assert_called_once_with(xblock_mock, html_data_mock, tmp_dir_mock)
        html_manipulator_mock.return_value.process_html.assert_called_once_with()
        context_manager_mock.assert_called_once_with(os_path_join_mock.return_value, 'w')
        os_path_join_mock.assert_called_once_with(tmp_dir_mock, 'index.html')
        context_manager_mock.return_value.__enter__.return_value.write.assert_called_once_with(
            html_manipulator_mock.return_value.process_html.return_value
        )

    @patch('openedx.features.offline_mode.storage_management.log.info')
    @patch('openedx.features.offline_mode.storage_management.ContentFile')
    @patch('openedx.features.offline_mode.storage_management.open')
    @patch('openedx.features.offline_mode.storage_management.get_storage')
    @patch('openedx.features.offline_mode.storage_management.OfflineContentGenerator.add_files_to_zip_recursively')
    @patch('openedx.features.offline_mode.storage_management.ZipFile')
    def test_create_zip_file(
        self,
        zip_file_context_manager: MagicMock,
        add_files_to_zip_recursively_mock: MagicMock,
        storage_mock: MagicMock,
        open_context_manager_mock: MagicMock,
        content_file_mock: MagicMock,
        log_info_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'
        temp_dir_mock = 'temp_dir_mock'
        base_path_mock = 'base_path_mock'
        file_name_mock = 'file_name_mock'

        OfflineContentGenerator(xblock_mock, html_data_mock).create_zip_file(
            temp_dir_mock, base_path_mock, file_name_mock
        )

        zip_file_context_manager.assert_called_once_with(os.path.join(temp_dir_mock, file_name_mock), 'w')
        zip_file_context_manager.return_value.__enter__.return_value.write.assert_called_once_with(
            os.path.join(temp_dir_mock, 'index.html'), 'index.html'
        )
        add_files_to_zip_recursively_mock.assert_called_once_with(
            zip_file_context_manager.return_value.__enter__.return_value,
            current_base_path=os.path.join(temp_dir_mock, 'assets'),
            current_path_in_zip='assets',
        )
        open_context_manager_mock.assert_called_once_with(os.path.join(temp_dir_mock, file_name_mock), 'rb')
        content_file_mock.assert_called_once_with(
            open_context_manager_mock.return_value.__enter__.return_value.read.return_value
        )
        storage_mock.return_value.save.assert_called_once_with(
            os.path.join(base_path_mock + file_name_mock), content_file_mock.return_value
        )
        log_info_mock.assert_called_once_with(
            f'Offline content for {file_name_mock} has been generated.'
        )

    @patch('openedx.features.offline_mode.storage_management.os')
    def test_add_files_to_zip_recursively_successfully_for_file(
        self,
        os_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'
        zip_file_mock = Mock()
        current_base_path_mock = 'current_base_path_mock'
        current_path_in_zip_mock = 'current_path_in_zip_mock'
        resource_path_mock = 'resource_path_mock'
        os_mock.listdir.return_value = [resource_path_mock]

        expected_os_mock_path_join_calls = [
            call(current_base_path_mock, resource_path_mock),
            call(current_path_in_zip_mock, resource_path_mock)
        ]

        OfflineContentGenerator(xblock_mock, html_data_mock).add_files_to_zip_recursively(
            zip_file_mock, current_base_path_mock, current_path_in_zip_mock
        )

        os_mock.listdir.assert_called_once_with(current_base_path_mock)
        self.assertListEqual(os_mock.path.join.call_args_list, expected_os_mock_path_join_calls)
        zip_file_mock.write.assert_called_once_with(os_mock.path.join.return_value, os_mock.path.join.return_value)

    @patch('openedx.features.offline_mode.storage_management.OfflineContentGenerator.add_files_to_zip_recursively')
    @patch('openedx.features.offline_mode.storage_management.os.listdir')
    def test_add_files_to_zip_recursively_successfully_recursively_path(
        self,
        os_listdir_mock: MagicMock,
        add_files_to_zip_recursively_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'
        zip_file_mock = Mock()
        current_base_path_mock = 'current_base_path_mock'
        current_path_in_zip_mock = 'current_path_in_zip_mock'
        resource_path_mock = 'resource_path_mock'
        os_listdir_mock.listdir.return_value = [resource_path_mock]

        OfflineContentGenerator(xblock_mock, html_data_mock).add_files_to_zip_recursively(
            zip_file_mock, current_base_path_mock, current_path_in_zip_mock
        )

        add_files_to_zip_recursively_mock.assert_called_once_with(
            zip_file_mock, current_base_path_mock, current_path_in_zip_mock
        )

    @patch('openedx.features.offline_mode.storage_management.log.error')
    @patch('openedx.features.offline_mode.storage_management.os.listdir', side_effect=OSError)
    def test_add_files_to_zip_recursively_with_os_error(
        self,
        os_mock: MagicMock,
        log_error_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        html_data_mock = 'html_markup_data_mock'
        zip_file_mock = Mock()
        current_base_path_mock = 'current_base_path_mock'
        current_path_in_zip_mock = 'current_path_in_zip_mock'

        OfflineContentGenerator(xblock_mock, html_data_mock).add_files_to_zip_recursively(
            zip_file_mock, current_base_path_mock, current_path_in_zip_mock
        )

        os_mock.assert_called_once_with(current_base_path_mock)
        log_error_mock.assert_called_once_with(f'Error while reading the directory: {current_base_path_mock}')


class OfflineContentGeneratorFunctionalTestCase(CourseForOfflineTestCase):
    """
    Tests creating Offline Content in storage.
    """

    def setUp(self):
        super().setUp()
        self.html_data = '<p>Test HTML Content<p>'  # lint-amnesty, pylint: disable=attribute-defined-outside-init

    @patch('openedx.features.offline_mode.html_manipulator.save_mathjax_to_xblock_assets')
    def test_generate_offline_content(self, save_mathjax_to_xblock_assets_mock):
        OfflineContentGenerator(self.html_block, self.html_data).generate_offline_content()

        expected_offline_content_path = (
            'test_root/uploads/offline_content/course-v1:RaccoonGang+1+2024/HTML_xblock_for_Offline.zip'
        )

        save_mathjax_to_xblock_assets_mock.assert_called_once()
        self.assertTrue(os.path.exists(expected_offline_content_path))
        shutil.rmtree('test_root/uploads/offline_content/course-v1:RaccoonGang+1+2024', ignore_errors=True)

    def test_save_xblock_html_to_temp_dir(self):
        shutil.rmtree('test_root/assets', ignore_errors=True)
        temp_dir = 'test_root/'
        os.makedirs('test_root/assets/js/')
        OfflineContentGenerator(self.html_block, self.html_data).save_xblock_html(temp_dir)

        expected_index_html_path = 'test_root/index.html'
        expected_mathjax_static_path = os.path.join(temp_dir, MATHJAX_STATIC_PATH)

        self.assertTrue(os.path.exists(expected_index_html_path))
        self.assertTrue(os.path.exists(expected_mathjax_static_path))
        with open(expected_index_html_path, 'r') as content:
            html_data = content.read()
            self.assertIn(self.html_data, html_data)

        shutil.rmtree('test_root/assets', ignore_errors=True)
        os.remove(expected_index_html_path)
