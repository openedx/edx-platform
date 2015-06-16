# coding=UTF-8
"""
Performance tests for field overrides.
"""
import ddt
import itertools
import mock

from courseware.views import progress  # pylint: disable=import-error
from datetime import datetime
from django.conf import settings
from django.core.cache import get_cache
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edxmako.middleware import MakoMiddleware  # pylint: disable=import-error
from nose.plugins.attrib import attr
from pytz import UTC
from request_cache.middleware import RequestCache
from student.models import CourseEnrollment
from student.tests.factories import UserFactory  # pylint: disable=import-error
from xblock.core import XBlock
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, \
    TEST_DATA_SPLIT_MODULESTORE, TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.factories import check_mongo_calls, CourseFactory, check_sum_of_calls
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
    __test__ = False

    # TEST_DATA must be overridden by subclasses
    TEST_DATA = None

    def setUp(self):
        """
        Create a test client, course, and user.
        """
        super(FieldOverridePerformanceTestCase, self).setUp()

        self.request_factory = RequestFactory()
        self.student = UserFactory.create()
        self.request = self.request_factory.get("foo")
        self.request.user = self.student
        self.course = None

        MakoMiddleware().process_request(self.request)

    def setup_course(self, size):
        """
        Build a gradable course where each node has `size` children.
        """
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

    def instrument_course_progress_render(self, dataset_index, queries, reads, xblocks):
        """
        Renders the progress page, instrumenting Mongo reads and SQL queries.
        """
        self.setup_course(dataset_index + 1)

        # Switch to published-only mode to simulate the LMS
        with self.settings(MODULESTORE_BRANCH='published-only'):
            # Clear all caches before measuring
            for cache in settings.CACHES:
                get_cache(cache).clear()

            # Refill the metadata inheritance cache
            modulestore().get_course(self.course.id, depth=None)

            # We clear the request cache to simulate a new request in the LMS.
            RequestCache.clear_request_cache()

            with self.assertNumQueries(queries):
                with check_mongo_calls(reads):
                    with check_sum_of_calls(XBlock, ['__init__'], xblocks):
                        self.grade_course(self.course)

    @ddt.data(*itertools.product(('no_overrides', 'ccx'), range(3)))
    @ddt.unpack
    @override_settings(
        FIELD_OVERRIDE_PROVIDERS=(),
    )
    def test_field_overrides(self, overrides, dataset_index):
        """
        Test without any field overrides.
        """
        providers = {
            'no_overrides': (),
            'ccx': ('ccx.overrides.CustomCoursesForEdxOverrideProvider',)
        }
        with self.settings(FIELD_OVERRIDE_PROVIDERS=providers[overrides]):
            queries, reads, xblocks = self.TEST_DATA[overrides][dataset_index]
            self.instrument_course_progress_render(dataset_index, queries, reads, xblocks)


class TestFieldOverrideMongoPerformance(FieldOverridePerformanceTestCase):
    """
    Test cases for instrumenting field overrides against the Mongo modulestore.
    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE
    __test__ = True

    TEST_DATA = {
        'no_overrides': [
            (27, 7, 19), (135, 7, 131), (595, 7, 537)
        ],
        'ccx': [
            (27, 7, 47), (135, 7, 455), (595, 7, 2037)
        ],
    }


class TestFieldOverrideSplitPerformance(FieldOverridePerformanceTestCase):
    """
    Test cases for instrumenting field overrides against the Split modulestore.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE
    __test__ = True

    TEST_DATA = {
        'no_overrides': [
            (27, 4, 9), (135, 19, 54), (595, 84, 215)
        ],
        'ccx': [
            (27, 4, 9), (135, 19, 54), (595, 84, 215)
        ]
    }
