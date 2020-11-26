"""Tests the course modules and their functions"""


import itertools
import unittest
from datetime import datetime, timedelta

import ddt
from dateutil import parser
from django.conf import settings
from django.test import override_settings
from fs.memoryfs import MemoryFS
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from pytz import utc
from xblock.runtime import DictKeyValueStore, KvsFieldData

from openedx.core.lib.teams_config import TeamsConfig, DEFAULT_COURSE_RUN_MAX_TEAM_SIZE
import xmodule.course_module
from xmodule.modulestore.xml import ImportSystem, XMLModuleStore

ORG = 'test_org'
COURSE = 'test_course'

NOW = datetime.strptime('2013-01-01T01:00:00', '%Y-%m-%dT%H:%M:00').replace(tzinfo=utc)

_TODAY = datetime.now(utc)
_LAST_WEEK = _TODAY - timedelta(days=7)
_NEXT_WEEK = _TODAY + timedelta(days=7)


class CourseFieldsTestCase(unittest.TestCase):

    def test_default_start_date(self):
        self.assertEqual(
            xmodule.course_module.CourseFields.start.default,
            datetime(2030, 1, 1, tzinfo=utc)
        )


class DummySystem(ImportSystem):
    @patch('xmodule.modulestore.xml.OSFS', lambda dir: MemoryFS())
    def __init__(self, load_error_modules, course_id=None):

        xmlstore = XMLModuleStore("data_dir", source_dirs=[],
                                  load_error_modules=load_error_modules)
        if course_id is None:
            course_id = CourseKey.from_string('/'.join([ORG, COURSE, 'test_run']))
        course_dir = "test_dir"
        error_tracker = Mock()

        super(DummySystem, self).__init__(
            xmlstore=xmlstore,
            course_id=course_id,
            course_dir=course_dir,
            error_tracker=error_tracker,
            load_error_modules=load_error_modules,
            field_data=KvsFieldData(DictKeyValueStore()),
        )


def get_dummy_course(start, announcement=None, is_new=None, advertised_start=None, end=None, certs='end'):
    """Get a dummy course"""

    system = DummySystem(load_error_modules=True)

    def to_attrb(n, v):
        return '' if v is None else '{0}="{1}"'.format(n, v).lower()

    is_new = to_attrb('is_new', is_new)
    announcement = to_attrb('announcement', announcement)
    advertised_start = to_attrb('advertised_start', advertised_start)
    end = to_attrb('end', end)

    start_xml = '''
         <course org="{org}" course="{course}" display_organization="{org}_display" display_coursenumber="{course}_display"
                graceperiod="1 day" url_name="test"
                start="{start}"
                {announcement}
                {is_new}
                {advertised_start}
                {end}
                certificates_display_behavior="{certs}">
            <chapter url="hi" url_name="ch" display_name="CH">
                <html url_name="h" display_name="H">Two houses, ...</html>
            </chapter>
         </course>
     '''.format(
        org=ORG,
        course=COURSE,
        start=start,
        is_new=is_new,
        announcement=announcement,
        advertised_start=advertised_start,
        end=end,
        certs=certs,
    )

    return system.process_xml(start_xml)


class HasEndedMayCertifyTestCase(unittest.TestCase):
    """Double check the semantics around when to finalize courses."""

    def setUp(self):
        super(HasEndedMayCertifyTestCase, self).setUp()

        system = DummySystem(load_error_modules=True)
        #sample_xml = """
        # <course org="{org}" course="{course}" display_organization="{org}_display" display_coursenumber="{course}_display"
        #        graceperiod="1 day" url_name="test"
        #        start="2012-01-01T12:00"
        #        {end}
        #        certificates_show_before_end={cert}>
        #    <chapter url="hi" url_name="ch" display_name="CH">
        #        <html url_name="h" display_name="H">Two houses, ...</html>
        #    </chapter>
        # </course>
        #""".format(org=ORG, course=COURSE)
        past_end = (datetime.now() - timedelta(days=12)).strftime("%Y-%m-%dT%H:%M:00")
        future_end = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%dT%H:%M:00")
        self.past_show_certs = get_dummy_course("2012-01-01T12:00", end=past_end, certs='early_with_info')
        self.past_show_certs_no_info = get_dummy_course("2012-01-01T12:00", end=past_end, certs='early_no_info')
        self.past_noshow_certs = get_dummy_course("2012-01-01T12:00", end=past_end, certs='end')
        self.future_show_certs = get_dummy_course("2012-01-01T12:00", end=future_end, certs='early_with_info')
        self.future_show_certs_no_info = get_dummy_course("2012-01-01T12:00", end=future_end, certs='early_no_info')
        self.future_noshow_certs = get_dummy_course("2012-01-01T12:00", end=future_end, certs='end')
        #self.past_show_certs = system.process_xml(sample_xml.format(end=past_end, cert=True))
        #self.past_noshow_certs = system.process_xml(sample_xml.format(end=past_end, cert=False))
        #self.future_show_certs = system.process_xml(sample_xml.format(end=future_end, cert=True))
        #self.future_noshow_certs = system.process_xml(sample_xml.format(end=future_end, cert=False))

    def test_has_ended(self):
        """Check that has_ended correctly tells us when a course is over."""
        self.assertTrue(self.past_show_certs.has_ended())
        self.assertTrue(self.past_show_certs_no_info.has_ended())
        self.assertTrue(self.past_noshow_certs.has_ended())
        self.assertFalse(self.future_show_certs.has_ended())
        self.assertFalse(self.future_show_certs_no_info.has_ended())
        self.assertFalse(self.future_noshow_certs.has_ended())

    def test_may_certify(self):
        """Check that may_certify correctly tells us when a course may wrap."""
        self.assertTrue(self.past_show_certs.may_certify())
        self.assertTrue(self.past_noshow_certs.may_certify())
        self.assertTrue(self.past_show_certs_no_info.may_certify())
        self.assertTrue(self.future_show_certs.may_certify())
        self.assertTrue(self.future_show_certs_no_info.may_certify())
        self.assertFalse(self.future_noshow_certs.may_certify())


class CourseSummaryHasEnded(unittest.TestCase):
    """ Test for has_ended method when end date is missing timezone information. """

    def test_course_end(self):
        test_course = get_dummy_course("2012-01-01T12:00")
        bad_end_date = parser.parse("2012-02-21 10:28:45")
        summary = xmodule.course_module.CourseSummary(test_course.id, end=bad_end_date)
        self.assertTrue(summary.has_ended())


@ddt.ddt
class IsNewCourseTestCase(unittest.TestCase):
    """Make sure the property is_new works on courses"""

    def setUp(self):
        super(IsNewCourseTestCase, self).setUp()

        # Needed for test_is_newish
        datetime_patcher = patch.object(
            xmodule.course_metadata_utils, 'datetime',
            Mock(wraps=datetime)
        )
        mocked_datetime = datetime_patcher.start()
        mocked_datetime.now.return_value = NOW
        self.addCleanup(datetime_patcher.stop)

    @patch('xmodule.course_metadata_utils.datetime.now')
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

            # Non-parseable advertised starts are ignored in preference to actual starts
            ((day2, None, "Spring"), (day1, None, "Fall"), self.assertLess),
            ((day1, None, "Spring"), (day1, None, "Fall"), self.assertEqual),

            # Partially parsable advertised starts should take priority over start dates
            ((day2, None, "October 2013"), (day2, None, "October 2012"), self.assertLess),
            ((day2, None, "October 2013"), (day1, None, "October 2013"), self.assertEqual),

            # Parseable advertised starts take priority over start dates
            ((day1, None, day2), (day1, None, day1), self.assertLess),
            ((day2, None, day2), (day1, None, day2), self.assertEqual),
        ]

        for a, b, assertion in dates:
            a_score = get_dummy_course(start=a[0], announcement=a[1], advertised_start=a[2]).sorting_score
            b_score = get_dummy_course(start=b[0], announcement=b[1], advertised_start=b[2]).sorting_score
            print("Comparing %s to %s" % (a, b))
            assertion(a_score, b_score)

    start_advertised_settings = [
        # start, advertised, result, is_still_default, date_time_result
        ('2012-12-02T12:00', None, 'Dec 02, 2012', False, u'Dec 02, 2012 at 12:00 UTC'),
        ('2012-12-02T12:00', '2011-11-01T12:00', 'Nov 01, 2011', False, u'Nov 01, 2011 at 12:00 UTC'),
        ('2012-12-02T12:00', 'Spring 2012', 'Spring 2012', False, 'Spring 2012'),
        ('2012-12-02T12:00', 'November, 2011', 'November, 2011', False, 'November, 2011'),
        (xmodule.course_module.CourseFields.start.default, None, 'TBD', True, 'TBD'),
        (xmodule.course_module.CourseFields.start.default, 'January 2014', 'January 2014', False, 'January 2014'),
    ]

    def test_start_date_is_default(self):
        for s in self.start_advertised_settings:
            d = get_dummy_course(start=s[0], advertised_start=s[1])
            self.assertEqual(d.start_date_is_still_default, s[3])

    def test_display_organization(self):
        descriptor = get_dummy_course(start='2012-12-02T12:00', is_new=True)
        self.assertNotEqual(descriptor.location.org, descriptor.display_org_with_default)
        self.assertEqual(descriptor.display_org_with_default, "{0}_display".format(ORG))

    def test_display_coursenumber(self):
        descriptor = get_dummy_course(start='2012-12-02T12:00', is_new=True)
        self.assertNotEqual(descriptor.location.course, descriptor.display_number_with_default)
        self.assertEqual(descriptor.display_number_with_default, "{0}_display".format(COURSE))

    def test_is_newish(self):
        descriptor = get_dummy_course(start='2012-12-02T12:00', is_new=True)
        assert descriptor.is_newish is True

        descriptor = get_dummy_course(start='2013-02-02T12:00', is_new=False)
        assert descriptor.is_newish is False

        descriptor = get_dummy_course(start='2013-02-02T12:00', is_new=True)
        assert descriptor.is_newish is True

        descriptor = get_dummy_course(start='2013-01-15T12:00')
        assert descriptor.is_newish is True

        descriptor = get_dummy_course(start='2013-03-01T12:00')
        assert descriptor.is_newish is True

        descriptor = get_dummy_course(start='2012-10-15T12:00')
        assert descriptor.is_newish is False

        descriptor = get_dummy_course(start='2012-12-31T12:00')
        assert descriptor.is_newish is True


class DiscussionTopicsTestCase(unittest.TestCase):

    def test_default_discussion_topics(self):
        d = get_dummy_course('2012-12-02T12:00')
        self.assertEqual({'General': {'id': 'i4x-test_org-test_course-course-test'}}, d.discussion_topics)


class TeamsConfigurationTestCase(unittest.TestCase):
    """
    Tests for the configuration of teams and the helper methods for accessing them.
    """

    def setUp(self):
        super(TeamsConfigurationTestCase, self).setUp()
        self.course = get_dummy_course('2012-12-02T12:00')
        self.course.teams_configuration = TeamsConfig(None)
        self.count = itertools.count()

    def add_team_configuration(self, max_team_size=3, topics=None):
        """ Add a team configuration to the course. """
        teams_config_data = {}
        teams_config_data["topics"] = [] if topics is None else topics
        if max_team_size is not None:
            teams_config_data["max_team_size"] = max_team_size
        self.course.teams_configuration = TeamsConfig(teams_config_data)

    def make_topic(self):
        """ Make a sample topic dictionary. """
        next_num = next(self.count)
        topic_id = "topic_id_{}".format(next_num)
        name = "Name {}".format(next_num)
        description = "Description {}".format(next_num)
        return {
            "name": name,
            "description": description,
            "id": topic_id,
            "type": "open",
            "max_team_size": None
        }

    def test_teams_enabled_new_course(self):
        # Make sure we can detect when no teams exist.
        self.assertFalse(self.course.teams_enabled)

        # add topics
        self.add_team_configuration(max_team_size=4, topics=[self.make_topic()])
        self.assertTrue(self.course.teams_enabled)

        # remove them again
        self.add_team_configuration(max_team_size=4, topics=[])
        self.assertFalse(self.course.teams_enabled)

    def test_teams_enabled_max_size_only(self):
        self.add_team_configuration(max_team_size=4)
        self.assertFalse(self.course.teams_enabled)

    def test_teams_enabled_no_max_size(self):
        self.add_team_configuration(max_team_size=None, topics=[self.make_topic()])
        self.assertTrue(self.course.teams_enabled)

    def test_teams_max_size_no_teams_configuration(self):
        self.assertEqual(
            self.course.teams_configuration.default_max_team_size,
            DEFAULT_COURSE_RUN_MAX_TEAM_SIZE,
        )

    def test_teams_max_size_with_teams_configured(self):
        size = 4
        self.add_team_configuration(max_team_size=size, topics=[self.make_topic(), self.make_topic()])
        self.assertTrue(self.course.teams_enabled)
        self.assertEqual(size, self.course.teams_configuration.default_max_team_size)

    def test_teamsets_no_config(self):
        self.assertEqual(self.course.teamsets, [])

    def test_teamsets_empty(self):
        self.add_team_configuration(max_team_size=4)
        self.assertEqual(self.course.teamsets, [])

    def test_teamsets_present(self):
        topics = [self.make_topic(), self.make_topic()]
        self.add_team_configuration(max_team_size=4, topics=topics)
        self.assertTrue(self.course.teams_enabled)
        expected_teamsets_data = [
            teamset.cleaned_data
            for teamset in self.course.teamsets
        ]
        self.assertEqual(expected_teamsets_data, topics)

    def test_teams_conf_cached_by_xblock_field(self):
        self.add_team_configuration(max_team_size=5, topics=[self.make_topic()])
        cold_cache_conf = self.course.teams_configuration
        warm_cache_conf = self.course.teams_configuration
        self.add_team_configuration(max_team_size=5, topics=[self.make_topic(), self.make_topic()])
        new_cold_cache_conf = self.course.teams_configuration
        new_warm_cache_conf = self.course.teams_configuration
        self.assertIs(cold_cache_conf, warm_cache_conf)
        self.assertIs(new_cold_cache_conf, new_warm_cache_conf)
        self.assertIsNot(cold_cache_conf, new_cold_cache_conf)


class SelfPacedTestCase(unittest.TestCase):
    """Tests for self-paced courses."""

    def setUp(self):
        super(SelfPacedTestCase, self).setUp()
        self.course = get_dummy_course('2012-12-02T12:00')

    def test_default(self):
        self.assertFalse(self.course.self_paced)


class CourseDescriptorTestCase(unittest.TestCase):
    """
    Tests for a select few functions from CourseDescriptor.

    I wrote these test functions in order to satisfy the coverage checker for
    PR #8484, which modified some code within CourseDescriptor. However, this
    class definitely isn't a comprehensive test case for CourseDescriptor, as
    writing a such a test case was out of the scope of the PR.
    """

    def setUp(self):
        """
        Initialize dummy testing course.
        """
        super(CourseDescriptorTestCase, self).setUp()
        self.course = get_dummy_course(start=_TODAY, end=_NEXT_WEEK)

    def test_clean_id(self):
        """
        Test CourseDescriptor.clean_id.
        """
        self.assertEqual(
            self.course.clean_id(),
            "course_ORSXG5C7N5ZGOL3UMVZXIX3DN52XE43FF52GK43UL5ZHK3Q="
        )
        self.assertEqual(
            self.course.clean_id(padding_char='$'),
            "course_ORSXG5C7N5ZGOL3UMVZXIX3DN52XE43FF52GK43UL5ZHK3Q$"
        )

    def test_has_started(self):
        """
        Test CourseDescriptor.has_started.
        """
        self.course.start = _LAST_WEEK
        self.assertTrue(self.course.has_started())
        self.course.start = _NEXT_WEEK
        self.assertFalse(self.course.has_started())

    def test_number(self):
        """
        Test CourseDescriptor.number.
        """
        self.assertEqual(self.course.number, COURSE)

    def test_set_default_certificate_available_date(self):
        """
        The certificate_available_date field should default to two days
        after the course end date.
        """
        expected_certificate_available_date = self.course.end + timedelta(days=2)
        self.assertEqual(expected_certificate_available_date, self.course.certificate_available_date)


class ProctoringProviderTestCase(unittest.TestCase):
    """
    Tests for ProctoringProvider, including the default value, validation, and inheritance behavior.
    """

    def setUp(self):
        """
        Initialize dummy testing course.
        """
        super(ProctoringProviderTestCase, self).setUp()
        self.proctoring_provider = xmodule.course_module.ProctoringProvider()

    def test_from_json_with_platform_default(self):
        """
        Test that a proctoring provider value equivalent to the platform
        default will pass validation.
        """
        default_provider = settings.PROCTORING_BACKENDS.get('DEFAULT')

        # we expect the validated value to be equivalent to the value passed in,
        # since there are no validation errors or missing data
        self.assertEqual(self.proctoring_provider.from_json(default_provider), default_provider)

    def test_from_json_with_invalid_provider(self):
        """
        Test that an invalid provider (i.e. not one configured at the platform level)
        throws a ValueError with the correct error message.
        """
        provider = 'invalid-provider'
        allowed_proctoring_providers = [u'mock', u'mock_proctoring_without_rules']

        with self.assertRaises(ValueError) as context_manager:
            self.proctoring_provider.from_json(provider)
        self.assertEqual(
            context_manager.exception.args[0],
            ['The selected proctoring provider, {}, is not a valid provider. Please select from one of {}.'
                .format(provider, allowed_proctoring_providers)]
        )

    def test_from_json_adds_platform_default_for_missing_provider(self):
        """
        Test that a value with no provider will inherit the default provider
        from the platform defaults.
        """
        default_provider = 'mock'

        self.assertEqual(self.proctoring_provider.from_json(None), default_provider)

    @override_settings(
        PROCTORING_BACKENDS={
            'mock': {},
            'mock_proctoring_without_rules': {}
        }
    )
    def test_default_with_no_platform_default(self):
        """
        Test that, when the platform defaults are not set, the default is correct.
        """
        self. assertEqual(self.proctoring_provider.default, None)

    @override_settings(PROCTORING_BACKENDS=None)
    def test_default_with_no_platform_configuration(self):
        """
        Test that, when the platform default is not specified, the default is correct.
        """
        default = self.proctoring_provider.default
        self.assertEqual(default, None)
