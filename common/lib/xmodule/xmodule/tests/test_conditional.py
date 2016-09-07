import json
import unittest

from fs.memoryfs import MemoryFS
from lxml import etree
from mock import Mock, patch

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xmodule.error_module import NonStaffErrorDescriptor
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from xmodule.modulestore.xml import ImportSystem, XMLModuleStore, CourseLocationManager
from xmodule.conditional_module import ConditionalDescriptor
from xmodule.tests import DATA_DIR, get_test_system, get_test_descriptor_system
from xmodule.tests.xml import factories as xml, XModuleXmlImportTest
from xmodule.validation import StudioValidationMessage
from xmodule.x_module import STUDENT_VIEW, AUTHOR_VIEW

ORG = 'test_org'
COURSE = 'conditional'      # name of directory with course data


class DummySystem(ImportSystem):

    @patch('xmodule.modulestore.xml.OSFS', lambda directory: MemoryFS())
    def __init__(self, load_error_modules):

        xmlstore = XMLModuleStore("data_dir", source_dirs=[], load_error_modules=load_error_modules)

        super(DummySystem, self).__init__(
            xmlstore=xmlstore,
            course_id=SlashSeparatedCourseKey(ORG, COURSE, 'test_run'),
            course_dir='test_dir',
            error_tracker=Mock(),
            load_error_modules=load_error_modules,
        )

    def render_template(self, template, context):
        raise Exception("Shouldn't be called")


class ConditionalModuleFactory(xml.XmlImportFactory):
    """
    Factory for generating ConditionalModule for testing purposes
    """
    tag = 'conditional'


class ConditionalFactory(object):
    """
    A helper class to create a conditional module and associated source and child modules
    to allow for testing.
    """
    @staticmethod
    def create(system, source_is_error_module=False):
        """
        return a dict of modules: the conditional with a single source and a single child.
        Keys are 'cond_module', 'source_module', and 'child_module'.

        if the source_is_error_module flag is set, create a real ErrorModule for the source.
        """
        descriptor_system = get_test_descriptor_system()

        # construct source descriptor and module:
        source_location = Location("edX", "conditional_test", "test_run", "problem", "SampleProblem", None)
        if source_is_error_module:
            # Make an error descriptor and module
            source_descriptor = NonStaffErrorDescriptor.from_xml(
                'some random xml data',
                system,
                id_generator=CourseLocationManager(source_location.course_key),
                error_msg='random error message'
            )
        else:
            source_descriptor = Mock(name='source_descriptor')
            source_descriptor.location = source_location

        source_descriptor.runtime = descriptor_system
        source_descriptor.render = lambda view, context=None: descriptor_system.render(source_descriptor, view, context)

        # construct other descriptors:
        child_descriptor = Mock(name='child_descriptor')
        child_descriptor._xmodule.student_view.return_value.content = u'<p>This is a secret</p>'
        child_descriptor.student_view = child_descriptor._xmodule.student_view
        child_descriptor.displayable_items.return_value = [child_descriptor]
        child_descriptor.runtime = descriptor_system
        child_descriptor.xmodule_runtime = get_test_system()
        child_descriptor.render = lambda view, context=None: descriptor_system.render(child_descriptor, view, context)
        child_descriptor.location = source_location.replace(category='html', name='child')

        def load_item(usage_id, for_parent=None):  # pylint: disable=unused-argument
            """Test-only implementation of load_item that simply returns static xblocks."""
            return {
                child_descriptor.location: child_descriptor,
                source_location: source_descriptor
            }.get(usage_id)

        descriptor_system.load_item = load_item

        system.descriptor_runtime = descriptor_system

        # construct conditional module:
        cond_location = Location("edX", "conditional_test", "test_run", "conditional", "SampleConditional", None)
        field_data = DictFieldData({
            'data': '<conditional/>',
            'conditional_attr': 'attempted',
            'conditional_value': 'true',
            'xml_attributes': {'attempted': 'true'},
            'children': [child_descriptor.location],
        })

        cond_descriptor = ConditionalDescriptor(
            descriptor_system,
            field_data,
            ScopeIds(None, None, cond_location, cond_location)
        )
        cond_descriptor.xmodule_runtime = system
        system.get_module = lambda desc: desc
        cond_descriptor.get_required_module_descriptors = Mock(return_value=[source_descriptor])

        # return dict:
        return {'cond_module': cond_descriptor,
                'source_module': source_descriptor,
                'child_module': child_descriptor}


class ConditionalModuleBasicTest(unittest.TestCase):
    """
    Make sure that conditional module works, using mocks for
    other modules.
    """

    def setUp(self):
        super(ConditionalModuleBasicTest, self).setUp()
        self.test_system = get_test_system()

    def test_icon_class(self):
        '''verify that get_icon_class works independent of condition satisfaction'''
        modules = ConditionalFactory.create(self.test_system)
        for attempted in ["false", "true"]:
            for icon_class in ['other', 'problem', 'video']:
                modules['source_module'].is_attempted = attempted
                modules['child_module'].get_icon_class = lambda: icon_class
                self.assertEqual(modules['cond_module'].get_icon_class(), icon_class)

    def test_get_html(self):
        modules = ConditionalFactory.create(self.test_system)
        # because get_test_system returns the repr of the context dict passed to render_template,
        # we reverse it here
        html = modules['cond_module'].render(STUDENT_VIEW).content
        expected = modules['cond_module'].xmodule_runtime.render_template('conditional_ajax.html', {
            'ajax_url': modules['cond_module'].xmodule_runtime.ajax_url,
            'element_id': u'i4x-edX-conditional_test-conditional-SampleConditional',
            'depends': u'i4x-edX-conditional_test-problem-SampleProblem',
        })
        self.assertEquals(expected, html)

    def test_handle_ajax(self):
        modules = ConditionalFactory.create(self.test_system)
        modules['cond_module'].save()
        modules['source_module'].is_attempted = "false"
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        print "ajax: ", ajax
        html = ajax['html']
        self.assertFalse(any(['This is a secret' in item for item in html]))

        # now change state of the capa problem to make it completed
        modules['source_module'].is_attempted = "true"
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        modules['cond_module'].save()
        print "post-attempt ajax: ", ajax
        html = ajax['html']
        self.assertTrue(any(['This is a secret' in item for item in html]))

    def test_error_as_source(self):
        '''
        Check that handle_ajax works properly if the source is really an ErrorModule,
        and that the condition is not satisfied.
        '''
        modules = ConditionalFactory.create(self.test_system, source_is_error_module=True)
        modules['cond_module'].save()
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        html = ajax['html']
        self.assertFalse(any(['This is a secret' in item for item in html]))


class ConditionalModuleXmlTest(unittest.TestCase):
    """
    Make sure ConditionalModule works, by loading data in from an XML-defined course.
    """
    @staticmethod
    def get_system(load_error_modules=True):
        '''Get a dummy system'''
        return DummySystem(load_error_modules)

    def setUp(self):
        super(ConditionalModuleXmlTest, self).setUp()
        self.test_system = get_test_system()

    def get_course(self, name):
        """Get a test course by directory name.  If there's more than one, error."""
        print "Importing {0}".format(name)

        modulestore = XMLModuleStore(DATA_DIR, source_dirs=[name])
        courses = modulestore.get_courses()
        self.modulestore = modulestore
        self.assertEquals(len(courses), 1)
        return courses[0]

    def test_conditional_module(self):
        """Make sure that conditional module works"""

        print "Starting import"
        course = self.get_course('conditional_and_poll')

        print "Course: ", course
        print "id: ", course.id

        def inner_get_module(descriptor):
            if isinstance(descriptor, Location):
                location = descriptor
                descriptor = self.modulestore.get_item(location, depth=None)
            descriptor.xmodule_runtime = get_test_system()
            descriptor.xmodule_runtime.descriptor_runtime = descriptor._runtime  # pylint: disable=protected-access
            descriptor.xmodule_runtime.get_module = inner_get_module
            return descriptor

        # edx - HarvardX
        # cond_test - ER22x
        location = Location("HarvardX", "ER22x", "2013_Spring", "conditional", "condone")

        def replace_urls(text, staticfiles_prefix=None, replace_prefix='/static/', course_namespace=None):
            return text
        self.test_system.replace_urls = replace_urls
        self.test_system.get_module = inner_get_module

        module = inner_get_module(location)
        print "module: ", module
        print "module children: ", module.get_children()
        print "module display items (children): ", module.get_display_items()

        html = module.render(STUDENT_VIEW).content
        print "html type: ", type(html)
        print "html: ", html
        html_expect = module.xmodule_runtime.render_template(
            'conditional_ajax.html',
            {
                # Test ajax url is just usage-id / handler_name
                'ajax_url': '{}/xmodule_handler'.format(location.to_deprecated_string()),
                'element_id': u'i4x-HarvardX-ER22x-conditional-condone',
                'depends': u'i4x-HarvardX-ER22x-problem-choiceprob'
            }
        )
        self.assertEqual(html, html_expect)

        gdi = module.get_display_items()
        print "gdi=", gdi

        ajax = json.loads(module.handle_ajax('', ''))
        module.save()
        print "ajax: ", ajax
        html = ajax['html']
        self.assertFalse(any(['This is a secret' in item for item in html]))

        # Now change state of the capa problem to make it completed
        inner_module = inner_get_module(location.replace(category="problem", name='choiceprob'))
        inner_module.attempts = 1
        # Save our modifications to the underlying KeyValueStore so they can be persisted
        inner_module.save()

        ajax = json.loads(module.handle_ajax('', ''))
        module.save()
        print "post-attempt ajax: ", ajax
        html = ajax['html']
        self.assertTrue(any(['This is a secret' in item for item in html]))

    def test_conditional_module_with_empty_sources_list(self):
        """
        If a ConditionalDescriptor is initialized with an empty sources_list, we assert that the sources_list is set
        via generating UsageKeys from the values in xml_attributes['sources']
        """
        dummy_system = Mock()
        dummy_location = Location("edX", "conditional_test", "test_run", "conditional", "SampleConditional", None)
        dummy_scope_ids = ScopeIds(None, None, dummy_location, dummy_location)
        dummy_field_data = DictFieldData({
            'data': '<conditional/>',
            'xml_attributes': {'sources': 'i4x://HarvardX/ER22x/poll_question/T15_poll'},
            'children': None,
        })
        conditional = ConditionalDescriptor(
            dummy_system,
            dummy_field_data,
            dummy_scope_ids,
        )
        self.assertEqual(
            conditional.sources_list[0],
            conditional.location.course_key.make_usage_key_from_deprecated_string(conditional.xml_attributes['sources'])
        )

    def test_conditional_module_parse_sources(self):
        dummy_system = Mock()
        dummy_location = Location("edX", "conditional_test", "test_run", "conditional", "SampleConditional", None)
        dummy_scope_ids = ScopeIds(None, None, dummy_location, dummy_location)
        dummy_field_data = DictFieldData({
            'data': '<conditional/>',
            'xml_attributes': {'sources': 'i4x://HarvardX/ER22x/poll_question/T15_poll;i4x://HarvardX/ER22x/poll_question/T16_poll'},
            'children': None,
        })
        conditional = ConditionalDescriptor(
            dummy_system,
            dummy_field_data,
            dummy_scope_ids,
        )
        self.assertEqual(
            conditional.parse_sources(conditional.xml_attributes),
            ['i4x://HarvardX/ER22x/poll_question/T15_poll', 'i4x://HarvardX/ER22x/poll_question/T16_poll']
        )

    def test_conditional_module_parse_attr_values(self):
        root = '<conditional attempted="false"></conditional>'
        xml_object = etree.XML(root)
        definition = ConditionalDescriptor.definition_from_xml(xml_object, Mock())[0]
        expected_definition = {
            'show_tag_list': [],
            'conditional_attr': 'attempted',
            'conditional_value': 'false',
            'conditional_message': ''
        }

        self.assertEqual(definition, expected_definition)

    def test_presence_attributes_in_xml_attributes(self):
        modules = ConditionalFactory.create(self.test_system)
        modules['cond_module'].save()
        modules['cond_module'].definition_to_xml(Mock())
        expected_xml_attributes = {
            'attempted': 'true',
            'message': '{link} must be attempted before this will become visible.',
            'sources': ''
        }
        self.assertDictEqual(modules['cond_module'].xml_attributes, expected_xml_attributes)


class ConditionalModuleStudioTest(XModuleXmlImportTest):
    """
    Unit tests for how conditional test interacts with Studio.
    """

    def setUp(self):
        super(ConditionalModuleStudioTest, self).setUp()
        course = xml.CourseFactory.build()
        sequence = xml.SequenceFactory.build(parent=course)
        conditional = ConditionalModuleFactory(
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
        self.assertIn('This is a secret HTML', html)

        context = create_studio_context(self.sequence, True)
        html = self.module_system.render(self.conditional, AUTHOR_VIEW, context).content
        self.assertNotIn('This is a secret HTML', html)

    def test_non_editable_settings(self):
        """
        Test the settings that are marked as "non-editable".
        """
        non_editable_metadata_fields = self.conditional.non_editable_metadata_fields
        self.assertIn(ConditionalDescriptor.due, non_editable_metadata_fields)
        self.assertIn(ConditionalDescriptor.is_practice_exam, non_editable_metadata_fields)
        self.assertIn(ConditionalDescriptor.is_time_limited, non_editable_metadata_fields)
        self.assertIn(ConditionalDescriptor.default_time_limit_minutes, non_editable_metadata_fields)
        self.assertIn(ConditionalDescriptor.show_tag_list, non_editable_metadata_fields)

    def test_validation_messages(self):
        """
        Test the validation message for a correctly configured conditional.
        """
        self.conditional.sources_list = None
        validation = self.conditional.validate()
        self.assertEqual(
            validation.summary.text,
            u"This component has no source components configured yet."
        )
        self.assertEqual(validation.summary.type, StudioValidationMessage.NOT_CONFIGURED)
        self.assertEqual(validation.summary.action_class, 'edit-button')
        self.assertEqual(validation.summary.action_label, u"Configure list of sources")
