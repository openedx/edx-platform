"""
Tests for course_metadata_utils.
"""
from collections import namedtuple
from datetime import timedelta, datetime
from unittest import TestCase

from django.utils import timezone
from django.utils.translation import ugettext

from xmodule.course_metadata_utils import (
    clean_course_key,
    url_name_for_course_location,
    display_name_with_default,
    number_for_course_location,
    has_course_started,
    has_course_ended,
    DEFAULT_START_DATE,
    course_start_date_is_default,
    course_start_datetime_text,
    course_end_datetime_text,
    may_certify_for_course,
)
from xmodule.modulestore.tests.test_cross_modulestore_import_export import (
    MongoModulestoreBuilder,
    VersioningModulestoreBuilder,
    MixedModulestoreBuilder
)

from util.date_utils import strftime_localized


_TODAY = timezone.now()
_LAST_MONTH = _TODAY - timedelta(days=30)
_LAST_WEEK = _TODAY - timedelta(days=7)
_NEXT_WEEK = _TODAY + timedelta(days=7)


class CourseMetadataUtilsTestCase(TestCase):
    """
    Tests for course_metadata_utils.
    """

    def setUp(self):
        """
        Set up module store testing capabilities and initialize test courses.
        """
        super(CourseMetadataUtilsTestCase, self).setUp()

        mongo_builder = MongoModulestoreBuilder()
        split_builder = VersioningModulestoreBuilder()
        mixed_builder = MixedModulestoreBuilder([('mongo', mongo_builder), ('split', split_builder)])

        with mixed_builder.build_without_contentstore() as (__, mixed_store):
            with mixed_store.default_store('mongo'):
                self.demo_course = mixed_store.create_course(
                    org="edX",
                    course="DemoX.1",
                    run="Fall_2014",
                    user_id=-3,  # -3 refers to a "testing user"
                    fields={
                        "start": _LAST_MONTH,
                        "end": _LAST_WEEK
                    }
                )
            with mixed_store.default_store('split'):
                self.html_course = mixed_store.create_course(
                    org="UniversityX",
                    course="CS-203",
                    run="Y2096",
                    user_id=-3,  # -3 refers to a "testing user"
                    fields={
                        "start": _NEXT_WEEK,
                        "advertised_start": "2038-01-19 03:14:07",
                        "display_name": "Intro to <html>"
                    }
                )

    def test_course_metadata_utils(self):
        """
        Test every single function in course_metadata_utils.
        """
        FunctionTest = namedtuple('FunctionTest', 'function scenarios')  # pylint: disable=invalid-name
        TestScenario = namedtuple('TestScenario', 'arguments expected_return')  # pylint: disable=invalid-name

        function_tests = [
            FunctionTest(clean_course_key, [
                TestScenario(
                    (self.demo_course.id, '='),
                    "course_MVSFQL2EMVWW6WBOGEXUMYLMNRPTEMBRGQ======"
                ),
                TestScenario(
                    (self.html_course.id, '~'),
                    "course_MNXXK4TTMUWXMMJ2KVXGS5TFOJZWS5DZLAVUGUZNGIYDGK2ZGIYDSNQ~"
                ),
            ]),
            FunctionTest(url_name_for_course_location, [
                TestScenario((self.demo_course.location,), self.demo_course.location.name),
                TestScenario((self.html_course.location,), self.html_course.location.name),
            ]),
            FunctionTest(display_name_with_default, [
                TestScenario((self.demo_course,), "Empty"),
                TestScenario((self.html_course,), "Intro to &lt;html&gt;"),
            ]),
            FunctionTest(number_for_course_location, [
                TestScenario((self.demo_course.location,), "DemoX.1"),
                TestScenario((self.html_course.location,), "CS-203"),
            ]),
            FunctionTest(has_course_started, [
                TestScenario((self.demo_course.start,), True),
                TestScenario((self.html_course.start,), False),
            ]),
            FunctionTest(has_course_ended, [
                TestScenario((self.demo_course.end,), True),
                TestScenario((self.html_course.end,), False),
            ]),
            FunctionTest(course_start_date_is_default, [
                TestScenario((self.demo_course.start, self.demo_course.advertised_start), False),
                TestScenario((self.html_course.start, None), False),
                TestScenario((DEFAULT_START_DATE, self.demo_course.advertised_start), True),
                TestScenario((DEFAULT_START_DATE, self.html_course.advertised_start), False),
            ]),
            FunctionTest(course_start_datetime_text, [
                TestScenario(
                    (
                        datetime(1945, 02, 06, 4, 20, 00, tzinfo=timezone.UTC()),
                        self.demo_course.advertised_start,
                        'SHORT_DATE',
                        ugettext,
                        strftime_localized
                    ),
                    "Feb 06, 1945",
                ),
                TestScenario(
                    (
                        DEFAULT_START_DATE,
                        self.html_course.advertised_start,
                        'DATE_TIME',
                        ugettext,
                        strftime_localized
                    ),
                    "Jan 19, 2038 at 03:14 UTC",
                ),
                TestScenario(
                    (
                        DEFAULT_START_DATE,
                        None,
                        'DATE_TIME',
                        ugettext,
                        strftime_localized
                    ),
                    # Translators: TBD stands for 'To Be Determined' and is used when a course
                    # does not yet have an announced start date.
                    ugettext('TBD'),
                )
            ]),
            FunctionTest(course_end_datetime_text, [
                TestScenario(
                    (datetime(1945, 02, 06, 4, 20, 00, tzinfo=timezone.UTC()), 'DATE_TIME', strftime_localized),
                    "Feb 06, 1945 at 04:20 UTC"
                ),
                TestScenario(
                    (None, 'DATE_TIME', strftime_localized),
                    ""
                )
            ]),
            FunctionTest(may_certify_for_course, [
                TestScenario(('early_with_info', True, True), True),
                TestScenario(('early_no_info', False, False), True),
                TestScenario(('end', True, False), True),
                TestScenario(('end', False, True), True),
                TestScenario(('end', False, False), False),
            ]),
        ]
        for function_test in function_tests:
            for scenario in function_test.scenarios:
                self.assertEqual(
                    function_test.function(*scenario.arguments),
                    scenario.expected_return
                )
