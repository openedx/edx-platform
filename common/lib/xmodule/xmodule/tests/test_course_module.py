import unittest
from time import strptime, gmtime
from fs.memoryfs import MemoryFS

from mock import Mock, patch

from xmodule.modulestore.xml import ImportSystem, XMLModuleStore


ORG = 'test_org'
COURSE = 'test_course'

NOW = strptime('2013-01-01T01:00:00', '%Y-%m-%dT%H:%M:00')


class DummySystem(ImportSystem):
    @patch('xmodule.modulestore.xml.OSFS', lambda dir: MemoryFS())
    def __init__(self, load_error_modules):

        xmlstore = XMLModuleStore("data_dir", course_dirs=[],
                                  load_error_modules=load_error_modules)
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


class IsNewCourseTestCase(unittest.TestCase):
    """Make sure the property is_new works on courses"""
    @staticmethod
    def get_dummy_course(start, is_new=None, load_error_modules=True):
        """Get a dummy course"""

        system = DummySystem(load_error_modules)
        is_new = '' if is_new is None else 'is_new="{0}"'.format(is_new).lower()

        start_xml = '''
         <course org="{org}" course="{course}"
                graceperiod="1 day" url_name="test"
                start="{start}"
                {is_new}>
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
         </course>
         '''.format(org=ORG, course=COURSE, start=start, is_new=is_new)

        return system.process_xml(start_xml)

    @patch('xmodule.course_module.time.gmtime')
    def test_non_started_yet(self, gmtime_mock):
        descriptor = self.get_dummy_course(start='2013-01-05T12:00')
        gmtime_mock.return_value = NOW
        assert(descriptor.is_new == True)
        assert(descriptor.days_until_start == 4)

    @patch('xmodule.course_module.time.gmtime')
    def test_already_started(self, gmtime_mock):
        gmtime_mock.return_value = NOW

        descriptor = self.get_dummy_course(start='2012-12-02T12:00')
        assert(descriptor.is_new == False)
        assert(descriptor.days_until_start < 0)

    @patch('xmodule.course_module.time.gmtime')
    def test_is_new_set(self, gmtime_mock):
        gmtime_mock.return_value = NOW

        descriptor = self.get_dummy_course(start='2012-12-02T12:00', is_new=True)
        assert(descriptor.is_new == True)
        assert(descriptor.days_until_start < 0)

        descriptor = self.get_dummy_course(start='2013-02-02T12:00', is_new=False)
        assert(descriptor.is_new == False)
        assert(descriptor.days_until_start > 0)

        descriptor = self.get_dummy_course(start='2013-02-02T12:00', is_new=True)
        assert(descriptor.is_new == True)
        assert(descriptor.days_until_start > 0)
