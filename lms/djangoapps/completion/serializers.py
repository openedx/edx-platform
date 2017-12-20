"""
Serializers for the Completion API
"""

# pylint: disable=abstract-method

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import defaultdict

from rest_framework import serializers
import six
from xblock.core import XBlock
from xblock.completable import XBlockCompletionMode
from xblock.plugin import PluginMissingError

from .models import AggregateCompletion


def get_completion_mode(block):
    """
    Return the completion_mode of the specified block.

    Blocks with no explicit completion_mode are considered to be
    COMPLETABLE.
    """
    return getattr(block, "completion_mode", XBlockCompletionMode.COMPLETABLE)


def is_aggregation_name(category):
    """
    Returns True if the named category is a valid aggregation name.

    Currently, valid aggregators comprise the list of block types that have
    a completion_mode of XBlockCompletionMode.AGGREGATOR, but this may be
    expanded in the future.
    """
    try:
        cls = XBlock.load_class(category)
    except PluginMissingError:
        return False

    return get_completion_mode(cls) == XBlockCompletionMode.AGGREGATOR


class CourseAggregationAdapter(object):
    """
    A class to combine aggregations for a given course into a structure
    that works for the serializer.  Can be given a collection of
    AggregateCompletion objects, or a single AggregateCompletion at a time.
    The adapter automatically filters out objects that do not belong to the
    given user and course, or that pertain to aggregations that we are not
    interested in.  This is done to facilitate working with querysets that
    take in objects from multiple courses (or for multiple users) all at once.

    Usage:

    To create CourseAggregationAdapters for a user's courses with a given queryset:

        >>> from lms.djangoapps.completion.models import AggregateCompletion
        >>> from lms.djangoapps.completion.serializers import CourseAggregationAdapter
        >>> completions = AggregateCompletion.objects.filter(
        >>>     user=user,
        >>>     aggregation_name__in=['course', 'chapter', 'vertical']
        >>> )
        >>> adapters = []
        >>> for course_key in Enrollments.objects.filter(user=user, active=True):
        >>>     adapters.append(CourseAggregationAdapter(
        >>>         user=user,
        >>>         course_key=course_key,
        >>>         queryset=completions,
        >>>     ))

    To add an aggregation or iterable of aggregations to an adapter:

        >>> from lms.djangoapps.completion.serializers import CourseAggregationAdapter
        >>> adapter = CourseAggregationAdapter(
        >>>     user=user,
        >>>     course_key=course_key,
        >>> )
        >>> adapter.add_aggregate_completion(completion1)
        >>> adapter.update_aggregate_completions([completion2, completion3])

    The adapter or list of adapters can then be passed to the serializer for processing.
    """
    def __init__(self, user, course_key, queryset=None):
        self.user = user
        self.course_key = course_key
        self.aggregations = defaultdict(list)
        if queryset:
            self.update_aggregate_completions(queryset)

    def __getattr__(self, name):
        """
        Provide the serializer with access to custom aggregators
        """
        if is_aggregation_name(name):
            return self.aggregations.get(name, [])
        else:
            raise AttributeError

    def add_aggregate_completion(self, aggregation):
        """
        Add an aggregation to the CourseAggregationAdapter, checking
        whether it meets the criteria for user, course_key, and aggregation_name
        """
        if (aggregation.user, aggregation.course_key) == (self.user, self.course_key):
            if is_aggregation_name(aggregation.aggregation_name):
                self.aggregations[aggregation.aggregation_name].append(aggregation)

    def update_aggregate_completions(self, iterable):
        for aggregation in iterable:
            self.add_aggregate_completion(aggregation)

    @property
    def course(self):
        """
        The AggregateCompletion for the course as a whole.

        If no course completion exists, use a dummy completion
        """
        if self.aggregations['course']:
            return self.aggregations['course'][0]
        else:
            return AggregateCompletion(
                user=self.user,
                course_key=self.course_key,
                aggregation_name='course',
                earned=0.0,
                possible=None,
                percent=None,
            )

    @property
    def earned(self):
        return self.course.earned

    @property
    def possible(self):
        return self.course.possible

    @property
    def percent(self):
        return self.course.percent


class _CompletionSerializer(serializers.Serializer):
    """
    Inner serializer for actual completion data.
    """
    earned = serializers.FloatField()
    possible = serializers.FloatField()
    percent = serializers.FloatField()


class CourseCompletionSerializer(serializers.Serializer):
    """
    Serialize completions at the course level.
    """
    course_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')
    mean = serializers.FloatField()

    optional_fields = {'mean'}

    def __init__(self, instance, requested_fields=frozenset(), *args, **kwargs):
        super(CourseCompletionSerializer, self).__init__(instance, *args, **kwargs)
        for field in self.optional_fields - requested_fields:
            del self.fields[field]


class BlockCompletionSerializer(serializers.Serializer):
    """
    A serializer that represents nested aggregations of sub-graphs
    of xblocks.
    """
    course_key = serializers.CharField()
    block_key = serializers.CharField()
    completion = _CompletionSerializer(source='*')


def native_identifier(string):
    """
    Convert identifiers to the the native str type for the current version of
    python. This is required for the first argument to three-argument-`type()`.

    This function expects all identifiers comprise only ascii characters.
    """
    if six.PY2:
        if isinstance(string, unicode):
            # Python 2 identifiers are required to be ascii
            string = string.encode('ascii')
    elif isinstance(string, bytes):
        # Python 3 identifiers can technically be non-ascii, but don't.
        string = string.decode('ascii')
    return string


def course_completion_serializer_factory(requested_fields):
    """
    Create a CourseCompletionSerializer that nests appropriate
    BlockCompletionSerializers for the specified requested_fields.
    """
    dunder_dict = {
        field: BlockCompletionSerializer(many=True) for field in requested_fields
        if is_aggregation_name(field)
    }
    return type(
        native_identifier('CourseCompletionSerializerWithAggregates'),
        (CourseCompletionSerializer,),
        dunder_dict,
    )
