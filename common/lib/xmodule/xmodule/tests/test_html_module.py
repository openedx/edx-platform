import unittest

from mock import Mock

from xblock.field_data import DictFieldData
from xmodule.html_module import HtmlModule, HtmlDescriptor

from . import get_test_system, get_test_descriptor_system
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xblock.fields import ScopeIds


def instantiate_descriptor(**field_data):
    """
    Instantiate descriptor with most properties.
    """
    system = get_test_descriptor_system()
    course_key = SlashSeparatedCourseKey('org', 'course', 'run')
    usage_key = course_key.make_usage_key('html', 'SampleHtml')
    return system.construct_xblock_from_class(
        HtmlDescriptor,
        scope_ids=ScopeIds(None, None, usage_key, usage_key),
        field_data=DictFieldData(field_data),
    )


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


class HtmlDescriptorIndexingTestCase(unittest.TestCase):
    """
    Make sure that HtmlDescriptor can format data for indexing as expected.
    """

    def test_index_dictionary(self):
        sample_xml = '''
            <html>
                <p>Hello World!</p>
            </html>
        '''
        descriptor = instantiate_descriptor(data=sample_xml)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {"html_content": " Hello World! ", "display_name": "Text"},
            "content_type": "Text"
        })

        sample_xml_cdata = '''
            <html>
                <p>This has CDATA in it.</p>
                <![CDATA[This is just a CDATA!]]>
            </html>
        '''
        descriptor = instantiate_descriptor(data=sample_xml_cdata)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {"html_content": " This has CDATA in it. ", "display_name": "Text"},
            "content_type": "Text"
        })

        sample_xml_tab_spaces = '''
            <html>
                <p>     Text has spaces :)  </p>
            </html>
        '''
        descriptor = instantiate_descriptor(data=sample_xml_tab_spaces)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {"html_content": " Text has spaces :) ", "display_name": "Text"},
            "content_type": "Text"
        })

        sample_xml_comment = '''
            <html>
                <p>This has HTML comment in it.</p>
                <!-- Html Comment -->
            </html>
        '''
        descriptor = instantiate_descriptor(data=sample_xml_comment)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {"html_content": " This has HTML comment in it. ", "display_name": "Text"},
            "content_type": "Text"
        })

        sample_xml_mix_comment_cdata = '''
            <html>
                <!-- Beginning of the html -->
                <p>This has HTML comment in it.<!-- Commenting Content --></p>
                <!-- Here comes CDATA -->
                <![CDATA[This is just a CDATA!]]>
                <p>HTML end.</p>
            </html>
        '''
        descriptor = instantiate_descriptor(data=sample_xml_mix_comment_cdata)
        self.assertEqual(descriptor.index_dictionary(), {
            "content": {"html_content": " This has HTML comment in it. HTML end. ", "display_name": "Text"},
            "content_type": "Text"
        })
