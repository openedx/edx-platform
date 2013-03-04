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
    def get_dummy_course(start, announcement=None, is_new=None, advertised_start=None):
        """Get a dummy course"""

        system = DummySystem(load_error_modules=True)

        def to_attrb(n, v):
            return '' if v is None else '{0}="{1}"'.format(n, v).lower()

        is_new = to_attrb('is_new', is_new)
        announcement = to_attrb('announcement', announcement)
        advertised_start = to_attrb('advertised_start', advertised_start)

        start_xml = '''
         <course org="{org}" course="{course}"
                graceperiod="1 day" url_name="test"
                start="{start}"
                {announcement}
                {is_new}
                {advertised_start}>
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
         </course>
         '''.format(org=ORG, course=COURSE, start=start, is_new=is_new,
                    announcement=announcement, advertised_start=advertised_start)

        return system.process_xml(start_xml)

    @patch('xmodule.course_module.time.gmtime')
    def test_sorting_score(self, gmtime_mock):
        gmtime_mock.return_value = NOW

        day1 = '2012-01-01T12:00'
        day2 = '2012-01-02T12:00'

        dates = [
            # Announce date takes priority over actual start
            # and courses announced on a later date are newer
            # than courses announced for an earlier date
            ((day1, day2, None), (day1, day1, None), self.assertLess),
            ((day1, day1, None), (day2, day1, None), self.assertEqual),

            # Announce dates take priority over advertised starts
            ((day1, day2, day1), (day1, day1, day1), self.assertLess),
            ((day1, day1, day2), (day2, day1, day2), self.assertEqual),

            # Later start == newer course
            ((day2, None, None), (day1, None, None), self.assertLess),
            ((day1, None, None), (day1, None, None), self.assertEqual),

            # Non-parseable advertised starts are ignored in preference
            # to actual starts
            ((day2, None, "Spring 2013"), (day1, None, "Fall 2012"), self.assertLess),
            ((day1, None, "Spring 2013"), (day1, None, "Fall 2012"), self.assertEqual),

            # Parseable advertised starts take priority over start dates
            ((day1, None, day2), (day1, None, day1), self.assertLess),
            ((day2, None, day2), (day1, None, day2), self.assertEqual),

        ]

        data = []
        for a, b, assertion in dates:
            a_score = self.get_dummy_course(start=a[0], announcement=a[1], advertised_start=a[2]).sorting_score
            b_score = self.get_dummy_course(start=b[0], announcement=b[1], advertised_start=b[2]).sorting_score
            print "Comparing %s to %s" % (a, b)
            assertion(a_score, b_score)



    @patch('xmodule.course_module.time.gmtime')
    def test_is_newish(self, gmtime_mock):
        gmtime_mock.return_value = NOW

        descriptor = self.get_dummy_course(start='2012-12-02T12:00', is_new=True)
        assert(descriptor.is_newish is True)

        descriptor = self.get_dummy_course(start='2013-02-02T12:00', is_new=False)
        assert(descriptor.is_newish is False)

        descriptor = self.get_dummy_course(start='2013-02-02T12:00', is_new=True)
        assert(descriptor.is_newish is True)

        descriptor = self.get_dummy_course(start='2013-01-15T12:00')
        assert(descriptor.is_newish is True)

        descriptor = self.get_dummy_course(start='2013-03-00T12:00')
        assert(descriptor.is_newish is True)

        descriptor = self.get_dummy_course(start='2012-10-15T12:00')
        assert(descriptor.is_newish is False)

        descriptor = self.get_dummy_course(start='2012-12-31T12:00')
        assert(descriptor.is_newish is True)
