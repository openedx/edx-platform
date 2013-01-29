import unittest
from time import strptime
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
    def get_dummy_course(start, announcement=None, is_new=None):
        """Get a dummy course"""

        system = DummySystem(load_error_modules=True)

        def to_attrb(n, v):
            return '' if v is None else '{0}="{1}"'.format(n, v).lower()

        is_new = to_attrb('is_new', is_new)
        announcement = to_attrb('announcement', announcement)

        start_xml = '''
         <course org="{org}" course="{course}"
                graceperiod="1 day" url_name="test"
                start="{start}"
                {announcement}
                {is_new}>
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
         </course>
         '''.format(org=ORG, course=COURSE, start=start, is_new=is_new,
                    announcement=announcement)

        return system.process_xml(start_xml)

    @patch('xmodule.course_module.time.gmtime')
    def test_sorting_score(self, gmtime_mock):
        gmtime_mock.return_value = NOW
        dates = [('2012-10-01T12:00', '2012-09-01T12:00'),  # 0
                 ('2012-12-01T12:00', '2012-11-01T12:00'),  # 1
                 ('2013-02-01T12:00', '2012-12-01T12:00'),  # 2
                 ('2013-02-01T12:00', '2012-11-10T12:00'),  # 3
                 ('2013-02-01T12:00', None),                # 4
                 ('2013-03-01T12:00', None),                # 5
                 ('2013-04-01T12:00', None),                # 6
                 ('2012-11-01T12:00', None),                # 7
                 ('2012-09-01T12:00', None),                # 8
                 ('1990-01-01T12:00', None),                # 9
                 ('2013-01-02T12:00', None),                # 10
                 ('2013-01-10T12:00', '2012-12-31T12:00'),  # 11
                 ('2013-01-10T12:00', '2013-01-01T12:00'),  # 12
        ]

        data = []
        for i, d in enumerate(dates):
            descriptor = self.get_dummy_course(start=d[0], announcement=d[1])
            score = descriptor.sorting_score
            data.append((score, i))

        result = [d[1] for d in sorted(data)]
        assert(result == [12, 11, 2, 3, 1, 0, 6, 5, 4, 10, 7, 8, 9])


    @patch('xmodule.course_module.time.gmtime')
    def test_is_new(self, gmtime_mock):
        gmtime_mock.return_value = NOW

        descriptor = self.get_dummy_course(start='2012-12-02T12:00', is_new=True)
        assert(descriptor.is_new is True)

        descriptor = self.get_dummy_course(start='2013-02-02T12:00', is_new=False)
        assert(descriptor.is_new is False)

        descriptor = self.get_dummy_course(start='2013-02-02T12:00', is_new=True)
        assert(descriptor.is_new is True)

        descriptor = self.get_dummy_course(start='2013-01-15T12:00')
        assert(descriptor.is_new is True)

        descriptor = self.get_dummy_course(start='2013-03-00T12:00')
        assert(descriptor.is_new is True)

        descriptor = self.get_dummy_course(start='2012-10-15T12:00')
        assert(descriptor.is_new is False)

        descriptor = self.get_dummy_course(start='2012-12-31T12:00')
        assert(descriptor.is_new is True)
