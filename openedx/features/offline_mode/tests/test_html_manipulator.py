"""
Tests for the testing methods for prepare HTML content for offline using.
"""

from bs4 import BeautifulSoup
from unittest import TestCase
from unittest.mock import MagicMock, Mock, call, patch

from openedx.features.offline_mode.constants import MATHJAX_CDN_URL, MATHJAX_STATIC_PATH
from openedx.features.offline_mode.html_manipulator import HtmlManipulator


class HtmlManipulatorTestCase(TestCase):
    """
    Test case for the testing `HtmlManipulator` methods.
    """

    @patch('openedx.features.offline_mode.html_manipulator.HtmlManipulator._replace_iframe')
    @patch('openedx.features.offline_mode.html_manipulator.BeautifulSoup', return_value='soup_mock')
    @patch('openedx.features.offline_mode.html_manipulator.HtmlManipulator._copy_platform_fonts')
    @patch('openedx.features.offline_mode.html_manipulator.HtmlManipulator._replace_external_links')
    @patch('openedx.features.offline_mode.html_manipulator.HtmlManipulator._replace_mathjax_link')
    @patch('openedx.features.offline_mode.html_manipulator.HtmlManipulator._replace_static_links')
    @patch('openedx.features.offline_mode.html_manipulator.HtmlManipulator._replace_asset_links')
    def test_process_html(
        self,
        replace_asset_links_mock: MagicMock,
        replace_static_links_mock: MagicMock,
        replace_mathjax_link_mock: MagicMock,
        replace_external_links: MagicMock,
        copy_platform_fonts: MagicMock,
        beautiful_soup_mock: MagicMock,
        replace_iframe_mock: MagicMock,
    ) -> None:
        html_data_mock = 'html_data_mock'
        xblock_mock = Mock()
        temp_dir_mock = 'temp_dir_mock'
        html_manipulator = HtmlManipulator(xblock_mock, html_data_mock, temp_dir_mock)
        expected_result = 'soup_mock'

        result = html_manipulator.process_html()

        replace_asset_links_mock.assert_called_once_with()
        replace_static_links_mock.assert_called_once_with()
        replace_mathjax_link_mock.assert_called_once_with()
        replace_external_links.assert_called_once_with()
        copy_platform_fonts.assert_called_once_with()
        beautiful_soup_mock.assert_called_once_with(html_manipulator.html_data, 'html.parser')
        replace_iframe_mock.assert_called_once_with(beautiful_soup_mock.return_value)
        self.assertEqual(result, expected_result)

    @patch('openedx.features.offline_mode.html_manipulator.save_mathjax_to_xblock_assets')
    def test_replace_mathjax_link(self, save_mathjax_to_xblock_assets: MagicMock) -> None:
        html_data_mock = f'<script src="{MATHJAX_CDN_URL}"></script>'
        xblock_mock = Mock()
        temp_dir_mock = 'temp_dir_mock'
        html_manipulator = HtmlManipulator(xblock_mock, html_data_mock, temp_dir_mock)

        expected_html_data_after_replacing = f'<script src="{MATHJAX_STATIC_PATH}"></script>'

        self.assertEqual(html_manipulator.html_data, html_data_mock)

        html_manipulator._replace_mathjax_link()  # lint-amnesty, pylint: disable=protected-access

        save_mathjax_to_xblock_assets.assert_called_once_with(html_manipulator.temp_dir)
        self.assertEqual(html_manipulator.html_data, expected_html_data_after_replacing)

    @patch('openedx.features.offline_mode.html_manipulator.save_asset_file')
    def test_replace_static_links(self, save_asset_file_mock: MagicMock) -> None:
        html_data_mock = '<div class="teacher-image"><img src="/static/images/professor-sandel.jpg"/></div>'
        xblock_mock = Mock()
        temp_dir_mock = 'temp_dir_mock'
        html_manipulator = HtmlManipulator(xblock_mock, html_data_mock, temp_dir_mock)

        expected_html_data_after_replacing = (
            '<div class="teacher-image"><img src="assets/images/professor-sandel.jpg"/></div>'
        )

        self.assertEqual(html_manipulator.html_data, html_data_mock)

        html_manipulator._replace_static_links()  # lint-amnesty, pylint: disable=protected-access

        save_asset_file_mock.assert_called_once_with(
            html_manipulator.temp_dir,
            html_manipulator.xblock,
            '/static/images/professor-sandel.jpg',
            'images/professor-sandel.jpg',
        )
        self.assertEqual(html_manipulator.html_data, expected_html_data_after_replacing)

    @patch('openedx.features.offline_mode.html_manipulator.save_asset_file')
    def test_replace_asset_links(self, save_asset_file_mock: MagicMock) -> None:
        html_data_mock = '/assets/courseware/v1/5b628a18f2ee3303081ffe4d6ab64ee4/asset-v1:OpenedX+DemoX+DemoCourse+type@asset+block/Pendleton_Sinking_Ship.jpeg'  # lint-amnesty, pylint: disable=line-too-long
        xblock_mock = Mock()
        temp_dir_mock = 'temp_dir_mock'
        html_manipulator = HtmlManipulator(xblock_mock, html_data_mock, temp_dir_mock)

        expected_html_data_after_replacing = (
            'assets/courseware/v1/5b628a18f2ee3303081ffe4d6ab64ee4/asset-v1:OpenedX+DemoX+DemoCourse+type@asset+block/Pendleton_Sinking_Ship.jpeg'  # lint-amnesty, pylint: disable=line-too-long
        )

        self.assertEqual(html_manipulator.html_data, html_data_mock)

        html_manipulator._replace_asset_links()  # lint-amnesty, pylint: disable=protected-access

        save_asset_file_mock.assert_called_once_with(
            html_manipulator.temp_dir,
            html_manipulator.xblock,
            html_data_mock,
            expected_html_data_after_replacing,
        )
        self.assertEqual(html_manipulator.html_data, expected_html_data_after_replacing)

    def test_replace_iframe(self):
        html_data_mock = """
            <iframe class="align-middle" title="${_('YouTube Video')}"
            src="" frameborder="0" allowfullscreen style="display:none;"></iframe>
        """
        soup = BeautifulSoup(html_data_mock, 'html.parser')
        expected_html_markup = """<p><a href="">${_('YouTube Video')}</a></p>"""

        HtmlManipulator._replace_iframe(soup)  # lint-amnesty, pylint: disable=protected-access

        self.assertEqual(f'{soup.find_all("p")[0]}', expected_html_markup)

    @patch('openedx.features.offline_mode.html_manipulator.save_external_file')
    def test_replace_external_links(self, save_external_file_mock: MagicMock) -> None:
        xblock_mock = Mock()
        temp_dir_mock = 'temp_dir_mock'
        html_data_mock = """
            <img src="https://cdn.example.com/image.jpg" alt="Example Image">
            <script src="https://ajax.libs.jquery/3.6.0/jquery.min.js"></script>
        """

        html_manipulator = HtmlManipulator(xblock_mock, html_data_mock, temp_dir_mock)
        html_manipulator._replace_external_links()  # lint-amnesty, pylint: disable=protected-access

        self.assertEqual(save_external_file_mock.call_count, 2)

    @patch('openedx.features.offline_mode.html_manipulator.uuid.uuid4')
    @patch('openedx.features.offline_mode.html_manipulator.save_external_file')
    def test_replace_external_link(
        self,
        save_external_file_mock: MagicMock,
        uuid_mock: MagicMock,
    ) -> None:
        xblock_mock = Mock()
        temp_dir_mock = 'temp_dir_mock'
        html_data_mock = 'html_data_mock'
        external_url_mock = 'https://cdn.example.com/image.jpg'
        uuid_result_mock = '123e4567-e89b-12d3-a456-426655440000'
        uuid_mock.return_value = uuid_result_mock
        mock_match = MagicMock()
        mock_match.group.side_effect = [external_url_mock, 'jpg']

        expected_result = 'assets/external/123e4567-e89b-12d3-a456-426655440000.jpg'
        expected_save_external_file_args = [call(temp_dir_mock, external_url_mock, expected_result)]

        html_manipulator = HtmlManipulator(xblock_mock, html_data_mock, temp_dir_mock)
        result = html_manipulator._replace_external_link(mock_match)  # lint-amnesty, pylint: disable=protected-access

        self.assertListEqual(save_external_file_mock.call_args_list, expected_save_external_file_args)
        self.assertEqual(result, expected_result)
