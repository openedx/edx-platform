"""
Tests for VideoConfigService.
"""

import unittest
from unittest.mock import patch, MagicMock
from opaque_keys.edx.keys import CourseKey

from openedx.core.lib.xblock_services.video_config import VideoConfigService


class TestVideoConfigService(unittest.TestCase):
    """Test cases for VideoConfigService."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.course_id = CourseKey.from_string('course-v1:edx+test+2023')
        self.service = VideoConfigService(course_id=self.course_id)
    
    def test_init(self):
        """Test service initialization."""
        service = VideoConfigService()
        self.assertIsNone(service.course_id)
        
        service = VideoConfigService(course_id=self.course_id)
        self.assertEqual(service.course_id, self.course_id)
    
    # Tests for is_hls_playback_enabled method
    @patch('openedx.core.lib.xblock_services.video_config.log')
    def test_is_hls_playback_enabled_import_error(self, mock_log):
        """Test HLS playback enabled with import error."""
        with patch('openedx.core.lib.xblock_services.video_config.CourseWaffleFlag', side_effect=ImportError):
            result = self.service.is_hls_playback_enabled()
            self.assertFalse(result)  # Default value from edx-platform
            mock_log.warning.assert_called_once()
    
    def test_is_hls_playback_enabled_success(self):
        """Test HLS playback enabled success."""
        result = self.service.is_hls_playback_enabled()
        # Currently returns False due to placeholder implementation
        self.assertFalse(result)
    
    # Tests for get_branding_info method
    @patch('openedx.core.lib.xblock_services.video_config.log')
    def test_get_branding_info_import_error(self, mock_log):
        """Test branding info with import error."""
        with patch('openedx.core.lib.xblock_services.video_config.CourseWaffleFlag', side_effect=ImportError):
            result = self.service.get_branding_info()
            expected = {
                'logo_url': None,
                'logo_alt_text': None,
                'favicon_url': None
            }
            self.assertEqual(result, expected)
            mock_log.warning.assert_called_once()
    
    def test_get_branding_info_success(self):
        """Test branding info success."""
        result = self.service.get_branding_info()
        expected = {
            'logo_url': None,
            'logo_alt_text': None,
            'favicon_url': None
        }
        self.assertEqual(result, expected)
    
    # Tests for get_course_by_id method
    @patch('openedx.core.lib.xblock_services.video_config.log')
    def test_get_course_by_id_import_error(self, mock_log):
        """Test get course by ID with import error."""
        with patch('openedx.core.lib.xblock_services.video_config.CourseOverview', side_effect=ImportError):
            result = self.service.get_course_by_id(self.course_id)
            self.assertIsNone(result)
            mock_log.warning.assert_called_once()
    
    # Tests for get_course_organization method
    @patch('openedx.core.lib.xblock_services.video_config.log')
    def test_get_course_organization_import_error(self, mock_log):
        """Test get course organization with import error."""
        with patch('openedx.core.lib.xblock_services.video_config.CourseOverview', side_effect=ImportError):
            result = self.service.get_course_organization(self.course_id)
            self.assertIsNone(result)
            mock_log.warning.assert_called_once()
