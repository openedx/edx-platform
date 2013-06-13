import unittest

from mock import Mock

from xmodule.html_module import HtmlModule
from xmodule.modulestore import Location

from . import test_system

class HtmlModuleSubstitutionTestCase(unittest.TestCase):
    location = Location(["i4x", "edX", "toy", "html", "simple_html"])
    descriptor = Mock()

    def test_substitution_works(self):
        sample_xml = '''%%USER_ID%%'''
        module_data = {'data': sample_xml}
        module_system = test_system()
        module = HtmlModule(module_system, self.location, self.descriptor, module_data)
        self.assertEqual(module.get_html(), str(module_system.anonymous_student_id))


    def test_substitution_without_magic_string(self):
        sample_xml = '''
            <html>
                <p>Hi USER_ID!11!</p>
            </html>
        '''
        module_data = {'data': sample_xml}
        module = HtmlModule(test_system(), self.location, self.descriptor, module_data)
        self.assertEqual(module.get_html(), sample_xml)


    def test_substitution_without_anonymous_student_id(self):
        sample_xml = '''%%USER_ID%%'''
        module_data = {'data': sample_xml}
        module_system = test_system()
        module_system.anonymous_student_id = None
        module = HtmlModule(module_system, self.location, self.descriptor, module_data)
        self.assertEqual(module.get_html(), sample_xml)

