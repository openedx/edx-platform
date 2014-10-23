"""
Tests for edX Notes app.
"""
import unittest
from mock import patch, Mock
from edxnotes.decorators import edxnotes


@edxnotes
class TestProblem(object):
    """
    Test class (fake problem) decorated by edxnotes decorator.

    The purpose of this class is to imitate any problem.
    """
    def __init__(self):
        self.system = ''

    def get_html(self):
        """
        Imitate get_html in module.
        """
        return 'original_get_html'


class EdxNotesDecoratorTest(unittest.TestCase):
    """
    Tests for edxnotes decorator.
    """

    def setUp(self):
        self.problem = TestProblem()

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': True})
    def test_edxnotes_enabled(self):
        """
        Tests if get_html is wrapped when feature flag is on.
        """
        self.assertIn('edx-notes-wrapper', self.problem.get_html())

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_EDXNOTES': False})
    def test_edxnotes_disabled(self):
        """
        Tests if get_html is not wrapped when feature flag is off.
        """
        self.assertEqual('original_get_html', self.problem.get_html())

    def test_edxnotes_studio(self):
        """
        Tests if get_html is not wrapped when problem is rendered in Studio.
        """
        self.problem.system = Mock(is_author_mode=True)
        self.assertEqual('original_get_html', self.problem.get_html())
