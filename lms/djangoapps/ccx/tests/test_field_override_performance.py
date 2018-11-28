# coding=UTF-8
"""
Performance tests for field overrides.
"""
import itertools
from datetime import datetime, date

import ddt
import mock
import pytest
from ccx_keys.locator import CCXLocator
from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from courseware.testutils import FieldOverrideTestMixin
from courseware.views.views import progress
from django.conf import settings
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import caches
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edx_django_utils.cache import RequestCache
from lms.djangoapps.ccx.tests.factories import CcxFactory
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from pytz import UTC
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xblock.core import XBlock
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MONGO_MODULESTORE,
    TEST_DATA_SPLIT_MODULESTORE,
    ModuleStoreTestCase
)
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls, check_sum_of_calls
from xmodule.modulestore.tests.utils import ProceduralCourseTestMixin

QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES


@mock.patch.dict(
    'django.conf.settings.FEATURES',
    {
        'ENABLE_XBLOCK_VIEW_ENDPOINT': True,
    }
)
@ddt.ddt
class FieldOverridePerformanceTestCase(FieldOverrideTestMixin, ProceduralCourseTestMixin, ModuleStoreTestCase):
    """
    Base class for instrumenting SQL queries and Mongo reads for field override
    providers.
    """
    __test__ = False
    # Tell Django to clean out all databases, not just default
    multi_db = True
    shard = 7

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
        self.request.session = {}
        self.request.user = self.student
        messages = FallbackStorage(self.request)
        self.request._messages = messages  # pylint: disable=protected-access

        patcher = mock.patch('edxmako.request_context.get_current_request', return_value=self.request)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.course = None
        self.ccx = None

    def setup_course(self, size, enable_ccx, view_as_ccx):
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
            grading_policy=grading_policy,
            enable_ccx=enable_ccx,
        )
        self.populate_course(size)

        course_key = self.course.id
        if enable_ccx:
            self.ccx = CcxFactory.create(course_id=self.course.id)
            if view_as_ccx:
                course_key = CCXLocator.from_course_locator(self.course.id, self.ccx.id)

        CourseEnrollment.enroll(
            self.student,
            course_key
        )
        return CourseKey.from_string(unicode(course_key))

    def grade_course(self, course_key):
        """
        Renders the progress page for the given course.
        """
        return progress(
            self.request,
            course_id=unicode(course_key),
            student_id=self.student.id
        )

    def assertMongoCallCount(self, calls):
        """
        Assert that mongodb is queried ``calls`` times in the surrounded
        context.
        """
        return check_mongo_calls(calls)

    def assertXBlockInstantiations(self, instantiations):
        """
        Assert that exactly ``instantiations`` XBlocks are instantiated in
        the surrounded context.
        """
        return check_sum_of_calls(XBlock, ['__init__'], instantiations, instantiations, include_arguments=False)

    def instrument_course_progress_render(
            self, course_width, enable_ccx, view_as_ccx,
            sql_queries, mongo_reads,
    ):
        """
        Renders the progress page, instrumenting Mongo reads and SQL queries.
        """
        course_key = self.setup_course(course_width, enable_ccx, view_as_ccx)

        # Switch to published-only mode to simulate the LMS
        with self.settings(MODULESTORE_BRANCH='published-only'):
            # Clear all caches before measuring
            for cache in settings.CACHES:
                caches[cache].clear()

            # Refill the metadata inheritance cache
            get_course_in_cache(course_key)

            # We clear the request cache to simulate a new request in the LMS.
            RequestCache.clear_all_namespaces()

            # Reset the list of provider classes, so that our django settings changes
            # can actually take affect.
            OverrideFieldData.provider_classes = None

            with self.assertNumQueries(sql_queries, using='default', table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
                with self.assertNumQueries(0, using='student_module_history'):
                    with self.assertMongoCallCount(mongo_reads):
                        with self.assertXBlockInstantiations(1):
                            self.grade_course(course_key)

    @ddt.data(*itertools.product(('no_overrides', 'ccx'), range(1, 4), (True, False), (True, False)))
    @ddt.unpack
    @override_settings(
        XBLOCK_FIELD_DATA_WRAPPERS=[],
        MODULESTORE_FIELD_OVERRIDE_PROVIDERS=[],
    )
    def test_field_overrides(self, overrides, course_width, enable_ccx, view_as_ccx):
        """
        Test without any field overrides.
        """
        ContentTypeGatingConfig.objects.create(
            enabled=True,
            enabled_as_of=date(2018, 1, 1),
        )

        providers = {
            'no_overrides': (),
            'ccx': ('ccx.overrides.CustomCoursesForEdxOverrideProvider',)
        }
        if overrides == 'no_overrides' and view_as_ccx:
            pytest.skip("Can't view a ccx course if field overrides are disabled.")

        if not enable_ccx and view_as_ccx:
            pytest.skip("Can't view a ccx course if ccx is disabled on the course")

        if self.MODULESTORE == TEST_DATA_MONGO_MODULESTORE and view_as_ccx:
            pytest.skip("Can't use a MongoModulestore test as a CCX course")

        with self.settings(
            XBLOCK_FIELD_DATA_WRAPPERS=['lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap'],
            MODULESTORE_FIELD_OVERRIDE_PROVIDERS=providers[overrides],
        ):
            sql_queries, mongo_reads = self.TEST_DATA[
                (overrides, course_width, enable_ccx, view_as_ccx)
            ]
            self.instrument_course_progress_render(
                course_width, enable_ccx, view_as_ccx, sql_queries, mongo_reads,
            )


class TestFieldOverrideMongoPerformance(FieldOverridePerformanceTestCase):
    """
    Test cases for instrumenting field overrides against the Mongo modulestore.
    """
    MODULESTORE = TEST_DATA_MONGO_MODULESTORE
    __test__ = True

    TEST_DATA = {
        # (providers, course_width, enable_ccx, view_as_ccx): (
        #     # of sql queries to default,
        #     # of mongo queries,
        # )
        ('no_overrides', 1, True, False): (31, 1),
        ('no_overrides', 2, True, False): (31, 1),
        ('no_overrides', 3, True, False): (31, 1),
        ('ccx', 1, True, False): (31, 1),
        ('ccx', 2, True, False): (31, 1),
        ('ccx', 3, True, False): (31, 1),
        ('no_overrides', 1, False, False): (31, 1),
        ('no_overrides', 2, False, False): (31, 1),
        ('no_overrides', 3, False, False): (31, 1),
        ('ccx', 1, False, False): (31, 1),
        ('ccx', 2, False, False): (31, 1),
        ('ccx', 3, False, False): (31, 1),
    }


class TestFieldOverrideSplitPerformance(FieldOverridePerformanceTestCase):
    """
    Test cases for instrumenting field overrides against the Split modulestore.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE
    __test__ = True

    TEST_DATA = {
        ('no_overrides', 1, True, False): (31, 3),
        ('no_overrides', 2, True, False): (31, 3),
        ('no_overrides', 3, True, False): (31, 3),
        ('ccx', 1, True, False): (31, 3),
        ('ccx', 2, True, False): (31, 3),
        ('ccx', 3, True, False): (31, 3),
        ('ccx', 1, True, True): (32, 3),
        ('ccx', 2, True, True): (32, 3),
        ('ccx', 3, True, True): (32, 3),
        ('no_overrides', 1, False, False): (31, 3),
        ('no_overrides', 2, False, False): (31, 3),
        ('no_overrides', 3, False, False): (31, 3),
        ('ccx', 1, False, False): (31, 3),
        ('ccx', 2, False, False): (31, 3),
        ('ccx', 3, False, False): (31, 3),
    }
