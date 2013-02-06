import json
from path import path
import unittest
from fs.memoryfs import MemoryFS

from lxml import etree
from mock import Mock, patch
from collections import defaultdict

from xmodule.x_module import XMLParsingSystem, XModuleDescriptor
from xmodule.xml_module import is_pointer_tag
from xmodule.errortracker import make_error_tracker
from xmodule.modulestore import Location
from xmodule.modulestore.xml import ImportSystem, XMLModuleStore
from xmodule.modulestore.exceptions import ItemNotFoundError

from .test_export import DATA_DIR

ORG = 'test_org'
COURSE = 'conditional'	# name of directory with course data

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



class ConditionalModuleTest(unittest.TestCase):

    @staticmethod
    def get_system(load_error_modules=True):
        '''Get a dummy system'''
        return DummySystem(load_error_modules)

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
        course = self.get_course('conditional')

        print "Course: ", course
        print "id: ", course.id

        instance_states = dict(problem=None)
        shared_state = None

        def inner_get_module(descriptor):
            if isinstance(descriptor, Location):
                location = descriptor
                descriptor = self.modulestore.get_instance(course.id, location, depth=None)
            location = descriptor.location
            instance_state = instance_states.get(location.category,None)
            print "inner_get_module, location.category=%s, inst_state=%s" % (location.category, instance_state)
            return descriptor.xmodule_constructor(test_system)(instance_state, shared_state)

        location = Location(["i4x", "edX", "cond_test", "conditional","condone"])
        module = inner_get_module(location)

        def replace_urls(text, staticfiles_prefix=None, replace_prefix='/static/', course_namespace=None):
            return text
        test_system.replace_urls = replace_urls
        test_system.get_module = inner_get_module

        print "module: ", module

        html = module.get_html()
        print "html type: ", type(html)
        print "html: ", html
        html_expect = "{'ajax_url': 'courses/course_id/modx/a_location', 'element_id': 'i4x-edX-cond_test-conditional-condone', 'id': 'i4x://edX/cond_test/conditional/condone'}"
        self.assertEqual(html, html_expect)

        gdi =  module.get_display_items()
        print "gdi=", gdi

        ajax = json.loads(module.handle_ajax('',''))
        self.assertTrue('xmodule.conditional_module' in ajax['html'])
        print "ajax: ", ajax

        # now change state of the capa problem to make it completed
        instance_states['problem'] = json.dumps({'attempts':1})

        ajax = json.loads(module.handle_ajax('',''))
        self.assertTrue('This is a secret' in ajax['html'])
        print "post-attempt ajax: ", ajax


