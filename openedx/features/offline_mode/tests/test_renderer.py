"""
Tests for the testing xBlock renderers for Offline Mode.
"""

from openedx.features.offline_mode.renderer import XBlockRenderer
from openedx.features.offline_mode.tests.base import CourseForOfflineTestCase


class XBlockRendererTestCase(CourseForOfflineTestCase):
    """
    Test case for the testing `XBlockRenderer`.
    """

    def test_render_xblock_from_lms_html_block(self):
        xblock_renderer = XBlockRenderer(str(self.html_block.location), user=self.user)

        result = xblock_renderer.render_xblock_from_lms()

        self.assertIsNotNone(result)
        self.assertEqual(type(result), str)
        self.assertIn('HTML xblock for Offline', result)
        self.assertIn('<p>Test HTML Content<p>', result)

    def test_render_xblock_from_lms_problem_block(self):
        xblock_renderer = XBlockRenderer(str(self.problem_block.location), user=self.user)

        result = xblock_renderer.render_xblock_from_lms()

        self.assertIsNotNone(result)
        self.assertEqual(type(result), str)
        self.assertIn('Problem xblock for Offline', result)
