# lint-amnesty, pylint: disable=missing-module-docstring

import json
import unittest
from unittest.mock import Mock, patch

from django.conf import settings
from fs.memoryfs import MemoryFS
from lxml import etree
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from web_fragments.fragment import Fragment
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.conditional_module import ConditionalBlock
from xmodule.error_module import ErrorBlock
from xmodule.modulestore.xml import CourseLocationManager, ImportSystem, XMLModuleStore
from xmodule.tests import DATA_DIR, get_test_descriptor_system, get_test_system
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml import factories as xml
from xmodule.validation import StudioValidationMessage
from xmodule.x_module import AUTHOR_VIEW, STUDENT_VIEW

ORG = 'test_org'
COURSE = 'conditional'      # name of directory with course data


class DummySystem(ImportSystem):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring

    @patch('xmodule.modulestore.xml.OSFS', lambda directory: MemoryFS())
    def __init__(self, load_error_modules):

        xmlstore = XMLModuleStore("data_dir", source_dirs=[], load_error_modules=load_error_modules)

        super().__init__(
            xmlstore=xmlstore,
            course_id=CourseKey.from_string('/'.join([ORG, COURSE, 'test_run'])),
            course_dir='test_dir',
            error_tracker=Mock(),
            load_error_modules=load_error_modules,
        )

    def render_template(self, template, context):  # lint-amnesty, pylint: disable=method-hidden
        raise Exception("Shouldn't be called")


class ConditionalBlockFactory(xml.XmlImportFactory):
    """
    Factory for generating ConditionalBlock for testing purposes
    """
    tag = 'conditional'


class ConditionalFactory:
    """
    A helper class to create a conditional module and associated source and child modules
    to allow for testing.
    """
    @staticmethod
    def create(system, source_is_error_module=False, source_visible_to_staff_only=False):
        """
        return a dict of modules: the conditional with a single source and a single child.
        Keys are 'cond_module', 'source_module', and 'child_module'.

        if the source_is_error_module flag is set, create a real ErrorBlock for the source.
        """
        descriptor_system = get_test_descriptor_system()

        # construct source descriptor and module:
        source_location = BlockUsageLocator(CourseLocator("edX", "conditional_test", "test_run", deprecated=True),
                                            "problem", "SampleProblem", deprecated=True)
        if source_is_error_module:
            # Make an error descriptor and module
            source_descriptor = ErrorBlock.from_xml(
                'some random xml data',
                system,
                id_generator=CourseLocationManager(source_location.course_key),
                error_msg='random error message'
            )
        else:
            source_descriptor = Mock(name='source_descriptor')
            source_descriptor.location = source_location

        source_descriptor.visible_to_staff_only = source_visible_to_staff_only
        source_descriptor.runtime = descriptor_system
        source_descriptor.render = lambda view, context=None: descriptor_system.render(source_descriptor, view, context)

        # construct other descriptors:
        child_descriptor = Mock(name='child_descriptor')
        child_descriptor.visible_to_staff_only = False
        child_descriptor._xmodule.student_view.return_value = Fragment(content='<p>This is a secret</p>')  # lint-amnesty, pylint: disable=protected-access
        child_descriptor.student_view = child_descriptor._xmodule.student_view  # lint-amnesty, pylint: disable=protected-access
        child_descriptor.displayable_items.return_value = [child_descriptor]
        child_descriptor.runtime = descriptor_system
        child_descriptor.xmodule_runtime = get_test_system()
        child_descriptor.render = lambda view, context=None: descriptor_system.render(child_descriptor, view, context)
        child_descriptor.location = source_location.replace(category='html', name='child')

        def visible_to_nonstaff_users(desc):
            """
            Returns if the object is visible to nonstaff users.
            """
            return not desc.visible_to_staff_only

        def load_item(usage_id, for_parent=None):  # pylint: disable=unused-argument
            """Test-only implementation of load_item that simply returns static xblocks."""
            return {
                child_descriptor.location: child_descriptor,
                source_location: source_descriptor
            }.get(usage_id)

        descriptor_system.load_item = load_item

        system.descriptor_runtime = descriptor_system

        # construct conditional module:
        cond_location = BlockUsageLocator(CourseLocator("edX", "conditional_test", "test_run", deprecated=True),
                                          "conditional", "SampleConditional", deprecated=True)
        field_data = DictFieldData({
            'data': '<conditional/>',
            'conditional_attr': 'attempted',
            'conditional_value': 'true',
            'xml_attributes': {'attempted': 'true'},
            'children': [child_descriptor.location],
        })

        cond_descriptor = ConditionalBlock(
            descriptor_system,
            field_data,
            ScopeIds(None, None, cond_location, cond_location)
        )
        cond_descriptor.xmodule_runtime = system
        system.get_module = lambda desc: desc if visible_to_nonstaff_users(desc) else None
        cond_descriptor.get_required_blocks = [
            system.get_module(source_descriptor),
        ]

        # return dict:
        return {'cond_module': cond_descriptor,
                'source_module': source_descriptor,
                'child_module': child_descriptor}


class ConditionalBlockBasicTest(unittest.TestCase):
    """
    Make sure that conditional module works, using mocks for
    other modules.
    """

    def setUp(self):
        super().setUp()
        self.test_system = get_test_system()

    def test_icon_class(self):
        '''verify that get_icon_class works independent of condition satisfaction'''
        modules = ConditionalFactory.create(self.test_system)
        for attempted in ["false", "true"]:
            for icon_class in ['other', 'problem', 'video']:
                modules['source_module'].is_attempted = attempted
                modules['child_module'].get_icon_class = lambda: icon_class  # lint-amnesty, pylint: disable=cell-var-from-loop
                assert modules['cond_module'].get_icon_class() == icon_class

    def test_get_html(self):
        modules = ConditionalFactory.create(self.test_system)
        # because get_test_system returns the repr of the context dict passed to render_template,
        # we reverse it here
        html = modules['cond_module'].render(STUDENT_VIEW).content
        mako_service = modules['cond_module'].xmodule_runtime.service(modules['cond_module'], 'mako')
        expected = mako_service.render_template('conditional_ajax.html', {
            'ajax_url': modules['cond_module'].ajax_url,
            'element_id': 'i4x-edX-conditional_test-conditional-SampleConditional',
            'depends': 'i4x-edX-conditional_test-problem-SampleProblem',
        })
        assert expected == html

    def test_handle_ajax(self):
        modules = ConditionalFactory.create(self.test_system)
        modules['cond_module'].save()
        modules['source_module'].is_attempted = "false"
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        fragments = ajax['fragments']
        assert not any(('This is a secret' in item['content']) for item in fragments)

        # now change state of the capa problem to make it completed
        modules['source_module'].is_attempted = "true"
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        modules['cond_module'].save()
        fragments = ajax['fragments']
        assert any(('This is a secret' in item['content']) for item in fragments)

    def test_error_as_source(self):
        '''
        Check that handle_ajax works properly if the source is really an ErrorBlock,
        and that the condition is not satisfied.
        '''
        modules = ConditionalFactory.create(self.test_system, source_is_error_module=True)
        modules['cond_module'].save()
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        fragments = ajax['fragments']
        assert not any(('This is a secret' in item['content']) for item in fragments)

    @patch('xmodule.conditional_module.log')
    def test_conditional_with_staff_only_source_module(self, mock_log):
        modules = ConditionalFactory.create(
            self.test_system,
            source_visible_to_staff_only=True,
        )
        cond_module = modules['cond_module']
        cond_module.save()
        cond_module.is_attempted = "false"
        cond_module.handle_ajax('', '')
        assert not mock_log.warn.called
        assert None in cond_module.get_required_blocks


class ConditionalBlockXmlTest(unittest.TestCase):
    """
    Make sure ConditionalBlock works, by loading data in from an XML-defined course.
    """

    def setUp(self):
        super().setUp()
        self.test_system = get_test_system()
        self.modulestore = XMLModuleStore(DATA_DIR, source_dirs=['conditional_and_poll'])
        courses = self.modulestore.get_courses()
        assert len(courses) == 1
        self.course = courses[0]

    def get_module_for_location(self, location):
        descriptor = self.modulestore.get_item(location, depth=None)
        return self.test_system.get_module(descriptor)

    @patch('xmodule.x_module.descriptor_global_local_resource_url')
    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': False})
    def test_conditional_module(self, _):
        """Make sure that conditional module works"""
        # edx - HarvardX
        # cond_test - ER22x
        location = BlockUsageLocator(CourseLocator("HarvardX", "ER22x", "2013_Spring", deprecated=True),
                                     "conditional", "condone", deprecated=True)

        module = self.get_module_for_location(location)
        html = module.render(STUDENT_VIEW).content
        mako_service = module.xmodule_runtime.service(module, 'mako')
        html_expect = mako_service.render_template(
            'conditional_ajax.html',
            {
                # Test ajax url is just usage-id / handler_name
                'ajax_url': f'{str(location)}/xmodule_handler',
                'element_id': 'i4x-HarvardX-ER22x-conditional-condone',
                'depends': 'i4x-HarvardX-ER22x-problem-choiceprob'
            }
        )
        assert html == html_expect

        ajax = json.loads(module.handle_ajax('', ''))
        fragments = ajax['fragments']
        assert not any(('This is a secret' in item['content']) for item in fragments)

        # Now change state of the capa problem to make it completed
        inner_module = self.get_module_for_location(location.replace(category="problem", name='choiceprob'))
        inner_module.attempts = 1
        # Save our modifications to the underlying KeyValueStore so they can be persisted
        inner_module.save()

        ajax = json.loads(module.handle_ajax('', ''))
        fragments = ajax['fragments']
        assert any(('This is a secret' in item['content']) for item in fragments)

    def test_conditional_module_with_empty_sources_list(self):
        """
        If a ConditionalBlock is initialized with an empty sources_list, we assert that the sources_list is set
        via generating UsageKeys from the values in xml_attributes['sources']
        """
        dummy_system = Mock()
        dummy_location = BlockUsageLocator(CourseLocator("edX", "conditional_test", "test_run"),
                                           "conditional", "SampleConditional")
        dummy_scope_ids = ScopeIds(None, None, dummy_location, dummy_location)
        dummy_field_data = DictFieldData({
            'data': '<conditional/>',
            'xml_attributes': {'sources': 'i4x://HarvardX/ER22x/poll_question/T15_poll'},
            'children': None,
        })
        conditional = ConditionalBlock(
            dummy_system,
            dummy_field_data,
            dummy_scope_ids,
        )

        new_run = conditional.location.course_key.run  # lint-amnesty, pylint: disable=unused-variable
        assert conditional.sources_list[0] == BlockUsageLocator.from_string(conditional.xml_attributes['sources'])\
            .replace(run=dummy_location.course_key.run)

    def test_conditional_module_parse_sources(self):
        dummy_system = Mock()
        dummy_location = BlockUsageLocator(CourseLocator("edX", "conditional_test", "test_run"),
                                           "conditional", "SampleConditional")
        dummy_scope_ids = ScopeIds(None, None, dummy_location, dummy_location)
        dummy_field_data = DictFieldData({
            'data': '<conditional/>',
            'xml_attributes': {'sources': 'i4x://HarvardX/ER22x/poll_question/T15_poll;i4x://HarvardX/ER22x/poll_question/T16_poll'},  # lint-amnesty, pylint: disable=line-too-long
            'children': None,
        })
        conditional = ConditionalBlock(
            dummy_system,
            dummy_field_data,
            dummy_scope_ids,
        )
        assert conditional.parse_sources(conditional.xml_attributes) == ['i4x://HarvardX/ER22x/poll_question/T15_poll',
                                                                         'i4x://HarvardX/ER22x/poll_question/T16_poll']

    def test_conditional_module_parse_attr_values(self):
        root = '<conditional attempted="false"></conditional>'
        xml_object = etree.XML(root)
        definition = ConditionalBlock.definition_from_xml(xml_object, Mock())[0]
        expected_definition = {
            'show_tag_list': [],
            'conditional_attr': 'attempted',
            'conditional_value': 'false',
            'conditional_message': ''
        }

        assert definition == expected_definition

    def test_presence_attributes_in_xml_attributes(self):
        modules = ConditionalFactory.create(self.test_system)
        modules['cond_module'].save()
        modules['cond_module'].definition_to_xml(Mock())
        expected_xml_attributes = {
            'attempted': 'true',
            'message': 'You must complete {link} before you can access this unit.',
            'sources': ''
        }
        self.assertDictEqual(modules['cond_module'].xml_attributes, expected_xml_attributes)


class ConditionalBlockStudioTest(XModuleXmlImportTest):
    """
    Unit tests for how conditional test interacts with Studio.
    """

    def setUp(self):
        super().setUp()
        course = xml.CourseFactory.build()
        sequence = xml.SequenceFactory.build(parent=course)
        conditional = ConditionalBlockFactory(
            parent=sequence,
            attribs={
                'group_id_to_child': '{"0": "i4x://edX/xml_test_course/html/conditional_0"}'
            }
        )
        xml.HtmlFactory(parent=conditional, url_name='conditional_0', text='This is a secret HTML')

        self.course = self.process_xml(course)
        self.sequence = self.course.get_children()[0]
        self.conditional = self.sequence.get_children()[0]

        self.module_system = get_test_system()
        self.module_system.descriptor_runtime = self.course._runtime  # pylint: disable=protected-access

        user = Mock(username='ma', email='ma@edx.org', is_staff=False, is_active=True)
        self.conditional.bind_for_student(
            self.module_system,
            user.id
        )

    def test_render_author_view(self,):
        """
        Test the rendering of the Studio author view.
        """

        def create_studio_context(root_xblock, is_unit_page):
            """
            Context for rendering the studio "author_view".
            """
            return {
                'reorderable_items': set(),
                'root_xblock': root_xblock,
                'is_unit_page': is_unit_page
            }

        context = create_studio_context(self.conditional, False)
        html = self.module_system.render(self.conditional, AUTHOR_VIEW, context).content
        assert 'This is a secret HTML' in html

        context = create_studio_context(self.sequence, True)
        html = self.module_system.render(self.conditional, AUTHOR_VIEW, context).content
        assert 'This is a secret HTML' not in html

    def test_non_editable_settings(self):
        """
        Test the settings that are marked as "non-editable".
        """
        non_editable_metadata_fields = self.conditional.non_editable_metadata_fields
        assert ConditionalBlock.due in non_editable_metadata_fields

    def test_validation_messages(self):
        """
        Test the validation message for a correctly configured conditional.
        """
        self.conditional.sources_list = None
        validation = self.conditional.validate()
        assert validation.summary.text == 'This component has no source components configured yet.'
        assert validation.summary.type == StudioValidationMessage.NOT_CONFIGURED
        assert validation.summary.action_class == 'edit-button'
        assert validation.summary.action_label == 'Configure list of sources'
