'''
Created on May 7, 2013

@author: dmitchell
'''
import unittest
from xmodule import templates


class TemplateTests(unittest.TestCase):
    """
    Test finding and using the templates (boilerplates) for xblocks.
    """

    def test_get_templates(self):
        found = templates.all_templates()
        self.assertIsNotNone(found.get('course'))
        self.assertIsNotNone(found.get('about'))
        self.assertIsNotNone(found.get('html'))
        self.assertIsNotNone(found.get('problem'))
        self.assertEqual(len(found.get('course')), 0)
        self.assertEqual(len(found.get('about')), 0)
        self.assertGreaterEqual(len(found.get('html')), 2)
        self.assertGreaterEqual(len(found.get('problem')), 10)
        dropdown = None
        for template in found['problem']:
            self.assertIn('display_name', template)
            if template['display_name'] == 'Dropdown':
                dropdown = template
                break
        self.assertIsNotNone(dropdown)
        self.assertIn('markdown', dropdown)
        self.assertIn('data', dropdown)
        self.assertRegexpMatches(dropdown['markdown'], r'^Dropdown.*')
        self.assertRegexpMatches(dropdown['data'], r'<problem>\s*<p>Dropdown.*')

