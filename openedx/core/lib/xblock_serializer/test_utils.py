"""
Test the OLX serialization utils
"""
import unittest

import ddt
from opaque_keys.edx.keys import CourseKey

from . import utils


@ddt.ddt
class TestUtils(unittest.TestCase):
    """
    Test the OLX serialization utils
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
        olx_out = utils.rewrite_absolute_static_urls(olx_in, course_id)
        assert olx_out == olx_expected

    @ddt.unpack
    @ddt.data(
        ('''<problem>\n<script>ambiguous script\n</script></problem>''', False),
        ('''<problem>\n<script type="text/python">\npython\nscript\n</script></problem>''', True),
        ('''<problem>\n<script type='text/python'>\npython\nscript\n</script></problem>''', True),
        ('''<problem>\n<script type="loncapa/python">\npython\nscript\n</script></problem>''', True),
        ('''<problem>\n<script type='loncapa/python'>\npython\nscript\n</script></problem>''', True),
    )
    def test_has_python_script(self, olx: str, has_script: bool):
        """
        Test the _has_python_script() helper
        """
        assert utils._has_python_script(olx) == has_script  # pylint: disable=protected-access
