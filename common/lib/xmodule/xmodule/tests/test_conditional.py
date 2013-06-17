
import json
import unittest
from fs.memoryfs import MemoryFS
from ast import literal_eval
from mock import Mock, patch

from xmodule.error_module import NonStaffErrorDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.xml import ImportSystem, XMLModuleStore
from xmodule.conditional_module import ConditionalModule

from xmodule.tests.test_export import DATA_DIR

ORG = 'test_org'
COURSE = 'conditional'      # name of directory with course data

from . import test_system


class DummySystem(ImportSystem):

    @patch('xmodule.modulestore.xml.OSFS', lambda dir: MemoryFS())
    def __init__(self, load_error_modules):

        xmlstore = XMLModuleStore("data_dir", course_dirs=[], load_error_modules=load_error_modules)
        course_id = "/".join([ORG, COURSE, 'test_run'])
        course_dir = "test_dir"
        policy = {}
        error_tracker = Mock()
        parent_tracker = Mock()

        super(DummySystem, self).__init__(
            xmlstore,
            course_id,
            course_dir,
            policy,
            error_tracker,
            parent_tracker,
            load_error_modules=load_error_modules,
        )

    def render_template(self, template, context):
            raise Exception("Shouldn't be called")

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
        # construct source descriptor and module:
        source_location = Location(["i4x", "edX", "conditional_test", "problem", "SampleProblem"])
        if source_is_error_module:
            # Make an error descriptor and module
            source_descriptor = NonStaffErrorDescriptor.from_xml('some random xml data',
                                                                 system,
                                                                 org=source_location.org,
                                                                 course=source_location.course,
                                                                 error_msg='random error message')
            source_module = source_descriptor.xmodule(system)
        else:
            source_descriptor = Mock()
            source_descriptor.location = source_location
            source_module = Mock()

        # construct other descriptors:
        child_descriptor = Mock()
        cond_descriptor = Mock()
        cond_descriptor.get_required_module_descriptors = lambda: [source_descriptor, ]
        cond_descriptor.get_children = lambda: [child_descriptor, ]
        cond_descriptor.xml_attributes = {"attempted": "true"}

        # create child module:
        child_module = Mock()
        child_module.get_html = lambda: '<p>This is a secret</p>'
        child_module.displayable_items = lambda: [child_module]
        module_map = {source_descriptor: source_module, child_descriptor: child_module}
        system.get_module = lambda descriptor: module_map[descriptor]

        # construct conditional module:
        cond_location = Location(["i4x", "edX", "conditional_test", "conditional", "SampleConditional"])
        model_data = {'data': '<conditional/>', 'location': cond_location}
        cond_module = ConditionalModule(system, cond_descriptor, model_data)

        # return dict:
        return {'cond_module': cond_module,
                'source_module': source_module,
                'child_module': child_module }


class ConditionalModuleBasicTest(unittest.TestCase):
    """
    Make sure that conditional module works, using mocks for
    other modules.
    """

    def setUp(self):
        self.test_system = test_system()

    def test_icon_class(self):
        '''verify that get_icon_class works independent of condition satisfaction'''
        modules = ConditionalFactory.create(self.test_system)
        for attempted in ["false", "true"]:
            for icon_class in [ 'other', 'problem', 'video']:
                modules['source_module'].is_attempted = attempted
                modules['child_module'].get_icon_class = lambda: icon_class
                self.assertEqual(modules['cond_module'].get_icon_class(), icon_class)


    def test_get_html(self):
        modules = ConditionalFactory.create(self.test_system)
        # because test_system returns the repr of the context dict passed to render_template,
        # we reverse it here
        html = modules['cond_module'].get_html()
        html_dict = literal_eval(html)
        self.assertEqual(html_dict['element_id'], 'i4x-edX-conditional_test-conditional-SampleConditional')
        self.assertEqual(html_dict['id'], 'i4x://edX/conditional_test/conditional/SampleConditional')
        self.assertEqual(html_dict['depends'], 'i4x-edX-conditional_test-problem-SampleProblem')

    def test_handle_ajax(self):
        modules = ConditionalFactory.create(self.test_system)
        modules['source_module'].is_attempted = "false"
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        print "ajax: ", ajax
        html = ajax['html']
        self.assertFalse(any(['This is a secret' in item for item in html]))

        # now change state of the capa problem to make it completed
        modules['source_module'].is_attempted = "true"
        ajax = json.loads(modules['cond_module'].handle_ajax('', ''))
        print "post-attempt ajax: ", ajax
        html = ajax['html']
        self.assertTrue(any(['This is a secret' in item for item in html]))

    def test_error_as_source(self):
        '''
        Check that handle_ajax works properly if the source is really an ErrorModule,
        and that the condition is not satisfied.
        '''
        modules = ConditionalFactory.create(self.test_system, source_is_error_module=True)
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
        self.test_system = test_system()

    def get_course(self, name):
        """Get a test course by directory name.  If there's more than one, error."""
        print "Importing {0}".format(name)

        modulestore = XMLModuleStore(DATA_DIR, course_dirs=[name])
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
                descriptor = self.modulestore.get_instance(course.id, location, depth=None)
            return descriptor.xmodule(self.test_system)

        # edx - HarvardX
        # cond_test - ER22x
        location = Location(["i4x", "HarvardX", "ER22x", "conditional", "condone"])

        def replace_urls(text, staticfiles_prefix=None, replace_prefix='/static/', course_namespace=None):
            return text
        self.test_system.replace_urls = replace_urls
        self.test_system.get_module = inner_get_module

        module = inner_get_module(location)
        print "module: ", module
        print "module.conditions_map: ", module.conditions_map
        print "module children: ", module.get_children()
        print "module display items (children): ", module.get_display_items()

        html = module.get_html()
        print "html type: ", type(html)
        print "html: ", html
        html_expect = "{'ajax_url': 'courses/course_id/modx/a_location', 'element_id': 'i4x-HarvardX-ER22x-conditional-condone', 'id': 'i4x://HarvardX/ER22x/conditional/condone', 'depends': 'i4x-HarvardX-ER22x-problem-choiceprob'}"
        self.assertEqual(html, html_expect)

        gdi = module.get_display_items()
        print "gdi=", gdi

        ajax = json.loads(module.handle_ajax('', ''))
        print "ajax: ", ajax
        html = ajax['html']
        self.assertFalse(any(['This is a secret' in item for item in html]))

        # now change state of the capa problem to make it completed
        inner_get_module(Location('i4x://HarvardX/ER22x/problem/choiceprob')).attempts = 1

        ajax = json.loads(module.handle_ajax('', ''))
        print "post-attempt ajax: ", ajax
        html = ajax['html']
        self.assertTrue(any(['This is a secret' in item for item in html]))

