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
        anon_id = '123456789'

        module_system = get_test_system()
        module_system.substitute_keywords_with_data = Mock(return_value=anon_id)
        module = HtmlModule(self.descriptor, module_system, field_data, Mock())
        self.assertEqual(module.get_html(), anon_id)
