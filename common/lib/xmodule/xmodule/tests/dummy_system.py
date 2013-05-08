from . import test_system
import unittest
from xmodule.modulestore import Location
from xmodule.modulestore.xml import ImportSystem, XMLModuleStore
from xmodule.tests.test_export import DATA_DIR
from fs.memoryfs import MemoryFS
from mock import patch, Mock

class DummySystem(ImportSystem):

    @patch('xmodule.modulestore.xml.OSFS', lambda dir: MemoryFS())
    def __init__(self, load_error_modules, org, course):

        xmlstore = XMLModuleStore("data_dir", course_dirs=[], load_error_modules=load_error_modules)
        course_id = "/".join([org, course, 'test_run'])
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

class DummySystemUser(object):
    test_system = test_system()
    @staticmethod
    def get_import_system(org, course, load_error_modules=True):
        '''Get a dummy system'''
        return DummySystem(load_error_modules, org, course)

    def get_course(self, name):
        """Get a test course by directory name.  If there's more than one, error."""

        modulestore = XMLModuleStore(DATA_DIR, course_dirs=[name])
        courses = modulestore.get_courses()
        self.modulestore = modulestore
        self.assertEquals(len(courses), 1)
        return courses[0]

    def get_module_from_location(self, location, course):
        course = self.get_course(course)
        if not isinstance(location, Location):
            location = Location(location)
        descriptor = self.modulestore.get_instance(course.id, location, depth=None)
        return descriptor.xmodule(self.test_system)