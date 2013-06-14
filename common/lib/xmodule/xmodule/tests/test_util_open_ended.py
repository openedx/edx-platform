from .import get_test_system
from xmodule.modulestore import Location
from xmodule.modulestore.xml import XMLModuleStore
from xmodule.tests.test_export import DATA_DIR

OPEN_ENDED_GRADING_INTERFACE = {
    'url': 'blah/',
    'username': 'incorrect',
    'password': 'incorrect',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller'
}

S3_INTERFACE = {
    'aws_access_key': "",
    'aws_secret_key': "",
    "aws_bucket_name": "",
}


class MockQueryDict(dict):
    """
    Mock a query dict so that it can be used in test classes.  This will only work with the combinedopenended tests,
    and does not mock the full query dict, only the behavior that is needed there (namely get_list).
    """
    def getlist(self, key, default=None):
        try:
            return super(MockQueryDict, self).__getitem__(key)
        except KeyError:
            if default is None:
                return []
        return default


class DummyModulestore(object):
    """
    A mixin that allows test classes to have convenience functions to get a module given a location
    """
    get_test_system = get_test_system()

    def setup_modulestore(self, name):
        self.modulestore = XMLModuleStore(DATA_DIR, course_dirs=[name])

    def get_course(self, name):
        """Get a test course by directory name.  If there's more than one, error."""
        courses = self.modulestore.get_courses()
        return courses[0]

    def get_module_from_location(self, location, course):
        course = self.get_course(course)
        if not isinstance(location, Location):
            location = Location(location)
        descriptor = self.modulestore.get_instance(course.id, location, depth=None)
        return descriptor.xmodule(self.test_system)
