"""Tests for methods defined in util/misc.py"""


from unittest import TestCase

from xmodule.util.misc import escape_html_characters


class UtilHtmlEscapeTests(TestCase):
    """
    Tests for methods exposed in util/misc
    """

    final_content = " This is a paragraph. "

    def test_escape_html_comments(self):
        html_content = """
            <!--This is a comment. Comments are not displayed in the browser-->

            This is a paragraph.
            """
        self.assertEqual(escape_html_characters(html_content), self.final_content)

    def test_escape_cdata_comments(self):
        html_content = """
            <![CDATA[
                function matchwo(a,b)
                {
                if (a < b && a < 0) then
                  {
                  return 1;
                  }
                else
                  {
                  return 0;
                  }
                }
            ]]>

            This is a paragraph.
            """
        self.assertEqual(escape_html_characters(html_content), self.final_content)

    def test_escape_non_breaking_space(self):
        html_content = """
            &nbsp;&nbsp;
            &nbsp;
            <![CDATA[
                function matchwo(a,b)
                {
                if (a < b && a < 0) then
                  {
                  return 1;
                  }
                else
                  {
                  return 0;
                  }
                }
            ]]>
            This is a paragraph.&nbsp;
        """
        self.assertEqual(escape_html_characters(html_content), self.final_content)
