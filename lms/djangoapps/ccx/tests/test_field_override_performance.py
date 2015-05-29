# coding=UTF-8
"""
Performance tests for field overrides.
"""
import ddt
import mock

from courseware.views import progress  # pylint: disable=import-error
from datetime import datetime
from django.core.cache import cache
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edxmako.middleware import MakoMiddleware  # pylint: disable=import-error
from nose.plugins.attrib import attr
from pytz import UTC
from student.models import CourseEnrollment
from student.tests.factories import UserFactory  # pylint: disable=import-error
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, \
    TEST_DATA_SPLIT_MODULESTORE, TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.factories import check_mongo_calls, CourseFactory
from xmodule.modulestore.tests.utils import ProceduralCourseTestMixin


@attr('shard_1')
@mock.patch.dict(
    'django.conf.settings.FEATURES', {'ENABLE_XBLOCK_VIEW_ENDPOINT': True}
)
@ddt.ddt
class FieldOverridePerformanceTestCase(ProceduralCourseTestMixin,
                                       ModuleStoreTestCase):
    """
    Base class for instrumenting SQL queries and Mongo reads for field override
    providers.
    """
    def setUp(self):
        """
        Create a test client, course, and user.
        """
        super(FieldOverridePerformanceTestCase, self).setUp()

        self.request_factory = RequestFactory()
        self.student = UserFactory.create()
        self.request = self.request_factory.get("foo")
        self.request.user = self.student

        MakoMiddleware().process_request(self.request)

        # TEST_DATA must be overridden by subclasses, otherwise the test is
        # skipped.
        self.TEST_DATA = None

    def setup_course(self, size):
        grading_policy = {
            "GRADER": [
                {
                    "drop_count": 2,
                    "min_count": 12,
                    "short_label": "HW",
                    "type": "Homework",
                    "weight": 0.15
                },
                {
                    "drop_count": 2,
                    "min_count": 12,
                    "type": "Lab",
                    "weight": 0.15
                },
                {
                    "drop_count": 0,
                    "min_count": 1,
                    "short_label": "Midterm",
                    "type": "Midterm Exam",
                    "weight": 0.3
                },
                {
                    "drop_count": 0,
                    "min_count": 1,
                    "short_label": "Final",
                    "type": "Final Exam",
                    "weight": 0.4
                }
            ],
            "GRADE_CUTOFFS": {
                "Pass": 0.5
            }
        }

        self.course = CourseFactory.create(
            graded=True,
            start=datetime.now(UTC),
            grading_policy=grading_policy
        )
        self.populate_course(size)

        CourseEnrollment.enroll(
            self.student,
            self.course.id
        )

    def grade_course(self, course):
        """
        Renders the progress page for the given course.
        """
        return progress(
            self.request,
            course_id=course.id.to_deprecated_string(),
            student_id=self.student.id
        )

    def instrument_course_progress_render(self, dataset_index, queries, reads):
        """
        Renders the progress page, instrumenting Mongo reads and SQL queries.
        """
        self.setup_course(dataset_index + 1)

        # Clear the cache before measuring
        # TODO: remove once django cache is disabled in tests
        cache.clear()
        with self.assertNumQueries(queries):
            with check_mongo_calls(reads):
                self.grade_course(self.course)

    def run_if_subclassed(self, test_type, dataset_index):
        """
        Run the query/read instrumentation only if TEST_DATA has been
        overridden.
        """
        if not self.TEST_DATA:
            self.skipTest(
                "Test not properly configured. TEST_DATA must be overridden "
                "by a subclass."
            )

        queries, reads = self.TEST_DATA[test_type][dataset_index]
        self.instrument_course_progress_render(dataset_index, queries, reads)

    @ddt.data((0,), (1,), (2,))
    @ddt.unpack
    @override_settings(
        FIELD_OVERRIDE_PROVIDERS=(),
    )
    def test_instrument_without_field_override(self, dataset):
        """
        Test without any field overrides.
        """
        self.run_if_subclassed('no_overrides', dataset)

    @ddt.data((0,), (1,), (2,))
    @ddt.unpack
    @override_settings(
        FIELD_OVERRIDE_PROVIDERS=(
            'ccx.overrides.CustomCoursesForEdxOverrideProvider',
        ),
    )
    def test_instrument_with_field_override(self, dataset):
        """
        Test with the CCX field override enabled.
        """
        self.run_if_subclassed('ccx', dataset)


class TestFieldOverrideMongoPerformance(FieldOverridePerformanceTestCase):
    """
    Test cases for instrumenting field overrides against the Mongo modulestore.
    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE

    def setUp(self):
        """
        Set the modulestore and scaffold the test data.
        """
        super(TestFieldOverrideMongoPerformance, self).setUp()

        self.TEST_DATA = {
            'no_overrides': [
                (22, 6), (130, 6), (590, 6)
            ],
            'ccx': [
                (22, 6), (130, 6), (590, 6)
            ],
        }


class TestFieldOverrideSplitPerformance(FieldOverridePerformanceTestCase):
    """
    Test cases for instrumenting field overrides against the Split modulestore.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set the modulestore and scaffold the test data.
        """
        super(TestFieldOverrideSplitPerformance, self).setUp()

        self.TEST_DATA = {
            'no_overrides': [
                (22, 4), (130, 19), (590, 84)
            ],
            'ccx': [
                (22, 4), (130, 19), (590, 84)
            ]
        }
