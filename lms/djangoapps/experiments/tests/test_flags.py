"""
Tests for experimentation feature flags
"""

import pytz

import ddt
from crum import set_current_request
from dateutil import parser
from django.test.client import RequestFactory
from edx_django_utils.cache import RequestCache
from mock import patch
from opaque_keys.edx.keys import CourseKey

from experiments.factories import ExperimentKeyValueFactory
from experiments.flags import ExperimentWaffleFlag
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


@ddt.ddt
class ExperimentWaffleFlagTests(SharedModuleStoreTestCase):
    """ Tests for the ExperimentWaffleFlag class """
    def setUp(self):
        super().setUp()

        self.user = UserFactory()

        self.request = RequestFactory().request()
        self.request.session = {}
        self.request.site = SiteFactory()
        self.request.user = self.user
        self.addCleanup(set_current_request, None)
        set_current_request(self.request)

        self.flag = ExperimentWaffleFlag('experiments', 'test', num_buckets=2, experiment_id=0)
        self.key = CourseKey.from_string('a/b/c')

        bucket_patch = patch('experiments.flags.stable_bucketing_hash_group', return_value=1)
        self.addCleanup(bucket_patch.stop)
        bucket_patch.start()

        self.addCleanup(RequestCache.clear_all_namespaces)

    def get_bucket(self, track=False, active=True):
        with self.flag.override(active=active):
            return self.flag.get_bucket(course_key=self.key, track=track)

    def test_basic_happy_path(self):
        self.assertEqual(self.get_bucket(), 1)

    def test_no_request(self):
        set_current_request(None)
        self.assertEqual(self.get_bucket(), 0)

    def test_not_enabled(self):
        self.assertEqual(self.get_bucket(active=False), 0)

    @ddt.data(
        ('2012-01-06', None, 1),  # no enrollment (we allow normal bucketing in this case)
        ('2012-01-06', '2012-01-05', 0),  # enrolled before experiment
        ('2012-01-06', '2012-01-07', 1),  # enrolled after experiment
        (None, '2012-01-07', 1),  # no experiment date
        ('not-a-date', '2012-01-07', 0),  # bad experiment date
    )
    @ddt.unpack
    def test_enrollment_start(self, experiment_start, enrollment_created, expected_bucket):
        if enrollment_created:
            enrollment = CourseEnrollmentFactory(user=self.user, course_id='a/b/c')
            enrollment.created = parser.parse(enrollment_created).replace(tzinfo=pytz.UTC)
            enrollment.save()
        if experiment_start:
            ExperimentKeyValueFactory(experiment_id=0, key='enrollment_start', value=experiment_start)
        self.assertEqual(self.get_bucket(), expected_bucket)

    @ddt.data(
        (True, 0),
        (False, 1),
    )
    @ddt.unpack
    def test_bucket_override(self, active, expected_bucket):
        bucket_flag = CourseWaffleFlag('experiments', 'test.0')
        with bucket_flag.override(active=active):
            self.assertEqual(self.get_bucket(), expected_bucket)

    def test_tracking(self):
        # Run twice, with same request
        with patch('experiments.flags.segment') as segment_mock:
            self.assertEqual(self.get_bucket(track=True), 1)
            RequestCache.clear_all_namespaces()  # we want to force get_bucket to check session, not early exit
            self.assertEqual(self.get_bucket(track=True), 1)

        # Now test that we only sent the signal once, and with the correct properties
        self.assertEqual(segment_mock.track.call_count, 1)
        self.assertEqual(segment_mock.track.call_args, ((), {
            'user_id': self.user.id,
            'event_name': 'edx.bi.experiment.user.bucketed',
            'properties': {
                'site': self.request.site.domain,
                'app_label': 'experiments',
                'experiment': 'test',
                'bucket': 1,
                'course_id': 'a/b/c',
                'is_staff': self.user.is_staff,
            },
        }))

    def test_caching(self):
        self.assertEqual(self.get_bucket(active=True), 1)
        self.assertEqual(self.get_bucket(active=False), 1)  # still returns 1!

    def test_is_enabled(self):
        with patch('experiments.flags.ExperimentWaffleFlag.get_bucket', return_value=1):
            self.assertEqual(self.flag.is_enabled_without_course_context(), True)
            self.assertEqual(self.flag.is_enabled(self.key), True)
            self.assertEqual(self.flag.is_enabled(), True)
        with patch('experiments.flags.ExperimentWaffleFlag.get_bucket', return_value=0):
            self.assertEqual(self.flag.is_enabled_without_course_context(), False)
            self.assertEqual(self.flag.is_enabled(self.key), False)
            self.assertEqual(self.flag.is_enabled(), False)
