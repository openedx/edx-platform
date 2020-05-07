"""
Feature flag support for experiments
"""

import datetime
import logging
from contextlib import contextmanager

import dateutil
import pytz
from crum import get_current_request
from edx_django_utils.cache import RequestCache

from experiments.stable_bucketing import stable_bucketing_hash_group
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag
from track import segment

log = logging.getLogger(__name__)


class ExperimentWaffleFlag(CourseWaffleFlag):
    """
    ExperimentWaffleFlag handles logic around experimental bucketing and whitelisting.

    You'll have one main flag that gates the experiment. This allows you to control the scope
    of your experiment and always provides a quick kill switch.

    But you'll also have smaller related flags that can force bucketing certain users into
    specific buckets of your experiment. Those can be set using a waffle named like
    "main_flag.BUCKET_NUM" (e.g. "course_experience.animated_exy.0") to force
    users that pass the first main waffle check into a specific bucket experience.

    If you pass this flag a course key, tracking calls to segment will be made per-course-run
    (rather than one call overall) and will include the course key.

    You can also control whether the experiment only affects future enrollments by setting
    an ExperimentKeyValue model object with a key of 'enrollment_start' to the date of the
    first enrollments that should be bucketed.

    Bucket 0 is assumed to be the control bucket.

    See a HOWTO here: https://openedx.atlassian.net/wiki/spaces/AC/pages/1250623700/Bucketing+users+for+an+experiment

    When writing tests involving an ExperimentWaffleFlag you must not use the
    override_waffle_flag utility. That will only turn the experiment on or off and won't
    override bucketing. Instead use ExperimentWaffleFlag's override method which
    will do both. Example:

        with MY_EXPERIMENT_WAFFLE_FLAG.override(active=True, bucket=1):
            ...

    or as a decorator:

        @MY_EXPERIMENT_WAFFLE_FLAG.override(active=True, bucket=1)
        def test_my_experiment(self):
            ...

    """
    def __init__(self, waffle_namespace, flag_name, num_buckets=2, experiment_id=None, **kwargs):
        super().__init__(waffle_namespace, flag_name, **kwargs)
        self.num_buckets = num_buckets
        self.experiment_id = experiment_id
        self.bucket_flags = [
            CourseWaffleFlag(waffle_namespace, '{}.{}'.format(flag_name, bucket), flag_undefined_default=False)
            for bucket in range(num_buckets)
        ]

    def _cache_bucket(self, key, value):
        request_cache = RequestCache('experiments')
        request_cache.set(key, value)
        return value

    def _is_enrollment_inside_date_bounds(self, experiment_values, user, course_key):
        """ Returns True if the user's enrollment (if any) is valid for the configured experiment date range """
        from student.models import CourseEnrollment

        enrollment_start = experiment_values.get('enrollment_start')
        enrollment_end = experiment_values.get('enrollment_end')
        if not enrollment_start and not enrollment_end:
            return True  # early exit just to avoid any further lookups

        now = datetime.datetime.now(pytz.utc)
        enrollment = CourseEnrollment.get_enrollment(user, course_key)

        # If the user isn't enrolled, act like they would enroll right now (this keeps the pre-enroll and post-enroll
        # experiences the same, if they decide to enroll right now)
        enrollment_creation_date = enrollment.created if enrollment else now

        # Enrollment must be after any enrollment_start date, if specified
        if enrollment_start:
            try:
                start_date = dateutil.parser.parse(enrollment_start).replace(tzinfo=pytz.UTC)
            except ValueError:
                log.exception('Could not parse enrollment start date for experiment %d', self.experiment_id)
                return False
            if enrollment_creation_date < start_date:
                return False

        # Enrollment must be before any enrollment_end date, if specified
        if enrollment_end:
            try:
                end_date = dateutil.parser.parse(enrollment_end).replace(tzinfo=pytz.UTC)
            except ValueError:
                log.exception('Could not parse enrollment end date for experiment %d', self.experiment_id)
                return False
            if enrollment_creation_date >= end_date:
                return False

        # All good! Either because the key was not set or because the enrollment was valid
        return True

    def get_bucket(self, course_key=None, track=True):
        """
        Return which bucket number the specified user is in.

        Bucket 0 is assumed to be the control bucket and will be returned if the experiment is not enabled for
        this user and course.
        """
        # Keep some imports in here, because this class is commonly used at a module level, and we want to avoid
        # circular imports for any models.
        from experiments.models import ExperimentKeyValue

        request = get_current_request()
        if not request:
            return 0

        if not request.user.id:
            # We need username for stable bucketing and id for tracking, so just skip anonymous (not-logged-in) users
            return 0

        # Use course key in experiment name to separate caches and segment calls per-course-run
        experiment_name = self.namespaced_flag_name + ('.{}'.format(course_key) if course_key else '')

        # Check if we have a cache for this request already
        request_cache = RequestCache('experiments')
        cache_response = request_cache.get_cached_response(experiment_name)
        if cache_response.is_found:
            return cache_response.value

        # Check if the main flag is even enabled for this user and course.
        if not self.is_experiment_on(course_key):  # grabs user from the current request, if any
            return self._cache_bucket(experiment_name, 0)

        # Check if the enrollment should even be considered (if it started before the experiment wants, we ignore)
        if course_key and self.experiment_id is not None:
            values = ExperimentKeyValue.objects.filter(experiment_id=self.experiment_id).values('key', 'value')
            values = {pair['key']: pair['value'] for pair in values}

            if not self._is_enrollment_inside_date_bounds(values, request.user, course_key):
                return self._cache_bucket(experiment_name, 0)

        bucket = stable_bucketing_hash_group(experiment_name, self.num_buckets, request.user.username)

        # Now check if the user is forced into a particular bucket, using our subordinate bucket flags
        for i, bucket_flag in enumerate(self.bucket_flags):
            if bucket_flag.is_enabled(course_key):
                bucket = i
                break

        session_key = 'tracked.{}'.format(experiment_name)
        if track and hasattr(request, 'session') and session_key not in request.session:
            segment.track(
                user_id=request.user.id,
                event_name='edx.bi.experiment.user.bucketed',
                properties={
                    'site': request.site.domain,
                    'app_label': self.waffle_namespace.name,
                    'experiment': self.flag_name,
                    'course_id': str(course_key) if course_key else None,
                    'bucket': bucket,
                    'is_staff': request.user.is_staff,
                    'nonInteraction': 1,
                }
            )

            # Mark that we've recorded this bucketing, so that we don't do it again this session
            request.session[session_key] = True

        return self._cache_bucket(experiment_name, bucket)

    def is_enabled(self, course_key=None):
        return self.get_bucket(course_key) != 0

    def is_enabled_without_course_context(self):
        return self.is_enabled()

    def is_experiment_on(self, course_key=None):
        # If no course_key is supplied check the global flag irrespective of courses
        if course_key is None:
            return super().is_enabled_without_course_context()

        return super().is_enabled(course_key)

    @contextmanager
    def override(self, active=True, bucket=1):  # pylint: disable=arguments-differ
        # Let CourseWaffleFlag override the base waffle flag value
        with super().override(active=active):
            # Now override the experiment bucket value
            from mock import patch
            if not active:
                bucket = 0
            with patch.object(self, 'get_bucket', return_value=bucket):
                yield
