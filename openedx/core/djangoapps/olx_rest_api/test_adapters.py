"""
Test the OLX REST API adapters code
"""
import unittest

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.olx_rest_api import adapters


class TestAdapters(unittest.TestCase):
    """
    Test the OLX REST API adapters code
    """

    def test_rewrite_absolute_static_urls(self):
        """
        Test that rewrite_absolute_static_urls() can find and replace all uses
        of absolute Studio URLs in a course.

        Some criteria:
        - Rewriting only happens if the course ID is the same. If the absolute
          URL points to a different course, the new /static/foo.png form won't
          work.
        """
        # Note that this doesn't have to be well-formed OLX
        course_id = CourseKey.from_string("course-v1:TestCourse+101+2020")
        olx_in = """
        <problem>
            <img src="https://studio.example.com/asset-v1:TestCourse+101+2020+type@asset+block@SCI_1.2_Image_.png">
            <a href='https://studio.example.com/asset-v1:TestCourse+101+2020+type@asset+block@Québec.html'>
                View a file with accented characters in the filename.
            </a>
            <a href="https://studio.example.com/xblock/block-v1:foo">Not an asset link</a>.
            <img src="https://studio.example.com/asset-v1:OtherCourse+500+2020+type@asset+block@exclude_me.png">
        </problem>
        """
        olx_expected = """
        <problem>
            <img src="/static/SCI_1.2_Image_.png">
            <a href='/static/Québec.html'>
                View a file with accented characters in the filename.
            </a>
            <a href="https://studio.example.com/xblock/block-v1:foo">Not an asset link</a>.
            <img src="https://studio.example.com/asset-v1:OtherCourse+500+2020+type@asset+block@exclude_me.png">
        </problem>
        """
        olx_out = adapters.rewrite_absolute_static_urls(olx_in, course_id)
        self.assertEqual(olx_out, olx_expected)
