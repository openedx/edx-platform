"""
Tests for course_metadata_utils.
"""
from collections import namedtuple
from datetime import timedelta, datetime
from unittest import TestCase

from pytz import utc
from xmodule.block_metadata_utils import (
    url_name_for_block,
    display_name_with_default,
    display_name_with_default_escaped,
)
from xmodule.course_metadata_utils import (
    clean_course_key,
    number_for_course_location,
    has_course_started,
    has_course_ended,
    DEFAULT_START_DATE,
    course_start_date_is_default,
    may_certify_for_course,
)
from xmodule.modulestore.tests.utils import (
    MongoModulestoreBuilder,
    VersioningModulestoreBuilder,
    MixedModulestoreBuilder
)


_TODAY = datetime.now(utc)
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
                        "display_name": "Intro to <html>"
                    }
                )

    def test_course_metadata_utils(self):
        """
        Test every single function in course_metadata_utils.
        """

        def mock_strftime_localized(date_time, format_string):
            """
            Mock version of strftime_localized used for testing purposes.

            Because we don't have a real implementation of strftime_localized
            to work with (strftime_localized is provided by the XBlock runtime,
            which we don't have access to for this test case), we must declare
            this dummy implementation. This does NOT behave like a real
            strftime_localized should. It purposely returns a really dumb value
            that's only useful for testing purposes.

            Arguments:
                date_time (datetime): datetime to be formatted.
                format_string (str): format specifier. Valid values include:
                    - 'DATE_TIME'
                    - 'TIME'
                    - 'SHORT_DATE'
                    - 'LONG_DATE'

            Returns (str): format_string + " " + str(date_time)
            """
            if format_string in ['DATE_TIME', 'TIME', 'SHORT_DATE', 'LONG_DATE']:
                return format_string + " " + date_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                raise ValueError("Invalid format string :" + format_string)

        def noop_gettext(text):
            """Dummy implementation of gettext, so we don't need Django."""
            return text

        test_datetime = datetime(1945, 2, 6, 4, 20, 00, tzinfo=utc)
        advertised_start_parsable = "2038-01-19 03:14:07"

        FunctionTest = namedtuple('FunctionTest', 'function scenarios')  # pylint: disable=invalid-name
        TestScenario = namedtuple('TestScenario', 'arguments expected_return')  # pylint: disable=invalid-name

        function_tests = [
            FunctionTest(clean_course_key, [
                # Test with a Mongo course and '=' as padding.
                TestScenario(
                    (self.demo_course.id, '='),
                    "course_MVSFQL2EMVWW6WBOGEXUMYLMNRPTEMBRGQ======"
                ),
                # Test with a Split course and '~' as padding.
                TestScenario(
                    (self.html_course.id, '~'),
                    "course_MNXXK4TTMUWXMMJ2KVXGS5TFOJZWS5DZLAVUGUZNGIYDGK2ZGIYDSNQ~"
                ),
            ]),
            FunctionTest(url_name_for_block, [
                TestScenario((self.demo_course,), self.demo_course.location.name),
                TestScenario((self.html_course,), self.html_course.location.name),
            ]),
            FunctionTest(display_name_with_default_escaped, [
                # Test course with no display name.
                TestScenario((self.demo_course,), "Empty"),
                # Test course with a display name that contains characters that need escaping.
                TestScenario((self.html_course,), "Intro to &lt;html&gt;"),
            ]),
            FunctionTest(display_name_with_default, [
                # Test course with no display name.
                TestScenario((self.demo_course,), "Empty"),
                # Test course with a display name that contains characters that need escaping.
                TestScenario((self.html_course,), "Intro to <html>"),
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
                TestScenario((test_datetime, advertised_start_parsable), False),
                TestScenario((test_datetime, None), False),
                TestScenario((DEFAULT_START_DATE, advertised_start_parsable), False),
                TestScenario((DEFAULT_START_DATE, None), True),
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
                actual_return = function_test.function(*scenario.arguments)
                self.assertEqual(actual_return, scenario.expected_return)

        # Even though we don't care about testing mock_strftime_localized,
        # we still need to test it with a bad format string in order to
        # satisfy the coverage checker.
        with self.assertRaises(ValueError):
            mock_strftime_localized(test_datetime, 'BAD_FORMAT_SPECIFIER')
