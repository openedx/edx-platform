"""
Tests for xmodule.x_module.ResourceTemplates
"""
import unittest

from xmodule.x_module import ResourceTemplates


class ResourceTemplatesTests(unittest.TestCase):
    """
    Tests for xmodule.x_module.ResourceTemplates
    """
    def test_templates(self):
        expected = set([
            'latex_html.yaml',
            'zooming_image.yaml',
            'announcement.yaml',
            'anon_user_id.yaml'])
        got = set((t['template_id'] for t in TestClass.templates()))
        self.assertEqual(expected, got)

    def test_templates_no_suchdir(self):
        self.assertEqual(len(TestClass2.templates()), 0)

    def test_get_template(self):
        self.assertEqual(
            TestClass.get_template('latex_html.yaml')['template_id'],
            'latex_html.yaml')


class TestClass(ResourceTemplates):
    """
    Derives from the class under test for testing purposes.

    Since `ResourceTemplates` is intended to be used as a mixin, we need to
    derive a class from it in order to fill in some data it's expecting to find
    in its mro.
    """
    template_packages = [__name__]

    @classmethod
    def get_template_dir(cls):
        return 'templates/test'


class TestClass2(TestClass):
    """
    Like TestClass, but `get_template_dir` returns a directory that doesn't
    exist.

    See `TestClass`.
    """

    @classmethod
    def get_template_dir(cls):
        return 'foo'
