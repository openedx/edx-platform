import unittest

from mock import Mock

from xblock.field_data import DictFieldData
from xmodule.html_module import HtmlModule

from . import get_test_system

class HtmlModuleSubstitutionTestCase(unittest.TestCase):
    descriptor = Mock()

    def test_substitution_works(self):
        sample_xml = '''%%USER_ID%%'''
        field_data = DictFieldData({'data': sample_xml})
        module_system = get_test_system()
        module = HtmlModule(self.descriptor, module_system, field_data, Mock())
        self.assertEqual(module.get_html(), str(module_system.anonymous_student_id))


    def test_substitution_without_magic_string(self):
        sample_xml = '''
            <html>
                <p>Hi USER_ID!11!</p>
            </html>
        '''
        field_data = DictFieldData({'data': sample_xml})
        module_system = get_test_system()
        module = HtmlModule(self.descriptor, module_system, field_data, Mock())
        self.assertEqual(module.get_html(), sample_xml)


    def test_substitution_without_anonymous_student_id(self):
        sample_xml = '''%%USER_ID%%'''
        field_data = DictFieldData({'data': sample_xml})
        module_system = get_test_system()
        module_system.anonymous_student_id = None
        module = HtmlModule(self.descriptor, module_system, field_data, Mock())
        self.assertEqual(module.get_html(), sample_xml)


    def test_xblock_user_runtime_service(self):
        user_service = self.runtime.service(self, 'user')
        xblock_user = user_service.get_user()

        # Make sure that xblock_user exists.
        self.assertIsNotNone(xblock_user)

