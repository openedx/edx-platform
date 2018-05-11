"""
Model code for completion API, including django models and facade classes
wrapping progress extension models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from django.core.cache import cache
from edx_solutions_api_integration.courses.views import (
    _get_course_progress_metrics,
)
from edx_solutions_api_integration.utils import get_aggregate_exclusion_user_ids

from lazy import lazy
from opaque_keys.edx.keys import UsageKey
from progress.models import CourseModuleCompletion

from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


AGGREGATE_CATEGORIES = {
    'course',
    'chapter',
    'sequential',
    'vertical',
}

IGNORE_CATEGORIES = {
    # Non-completable types
    'discussion-course',
    'group-project',
    'discussion-forum',
    'eoc-journal',

    # GP v2 categories
    'gp-v2-project',
}


class CompletionDataMixin(object):
    """
    Common calculations for completion values of courses or blocks within
    courses.

    Classes using this mixin must implement:

        * self.stats (_Stats): An object representing the earned and possible
          values.
    """

    @lazy
    def earned(self):
        """
        The number of earned completions within self.block.
        """
        return float(self.stats.earned)

    @lazy
    def possible(self):
        """
        Return the maximum number of completions the user could earn in the
        course.
        """
        return float(self.stats.possible)

    @lazy
    def ratio(self):
        """
        Return the fraction of the course completed by the user.

        Ratio is returned as a float in the range [0.0, 1.0].
        """
        if self.possible == 0.0:
            ratio = 1.0
        else:
            ratio = self.earned / self.possible
        return ratio


class CourseCompletionFacade(CompletionDataMixin, object):
    """
    Facade wrapping progress.models.StudentProgress model.
    """

    _all_stats = None

    MEAN_CACHE_KEY_FORMAT = 'completion-api-v0.mean-completion.{course_key}'

    def __init__(self, inner):
        self._inner = inner
        self._completions_in_category = {}

    @lazy
    def stats(self):
        """
        Completion statistics for the current block
        """
        return self.all_stats[self.block_key]

    @lazy
    def block_key(self):
        """
        The block key for the course.
        """
        return CourseOverview.get_from_id(self.course_key).location

    @lazy
    def blocks(self):
        """
        Return an
        `openedx.core.lib.block_structure.block_structure.BlockStructureBlockData`
        collection which behaves as dict that maps
        `opaque_keys.edx.locator.BlockUsageLocator`s to
        `openedx.core.lib.block_structure.block_structure.BlockData` objects
        for all blocks in the course.
        """
        return get_course_blocks(
            self.user,
            self.block_key,
        )

    def _recurse_all_stats(self, block):
        """
        Descend through the course graph, collecting completion data for
        aggregate nodes.
        """
        if block.block_type in IGNORE_CATEGORIES:
            stats = _Stats.empty()
        elif block.block_type in AGGREGATE_CATEGORIES:
            stats = sum((self._recurse_all_stats(child) for child in self.blocks.get_children(block)), _Stats.empty())
            self._all_stats[block] = stats
        else:
            if block in self.completed_modules:
                earned = 1
            else:
                earned = 0
            stats = _Stats(earned=earned, possible=1)
        return stats

    @property
    def all_stats(self):
        """
        Return a dictionary mapping all aggregate nodes to their contained
        completion statics.
        """
        if self._all_stats is None:
            self._all_stats = {}
            self._recurse_all_stats(self.block_key)
        return self._all_stats

    def iter_block_keys_in_category(self, category):
        """
        Yields the UsageKey for all blocks of the specified category.
        """
        return (block for block in self.blocks if block.block_type == category)

    def get_completions_in_category(self, category):
        """
        Returns a list of BlockCompletions for each block of the requested category.
        """
        if category not in self._completions_in_category:
            completions = [
                BlockCompletion(self.user, block_key, self) for block_key in self.iter_block_keys_in_category(category)
            ]
            self._completions_in_category[category] = completions
        return self._completions_in_category[category]

    @lazy
    def completed_modules(self):
        """
        Returns a set of usage keys for modules that have been completed.
        """
        modules = CourseModuleCompletion.objects.filter(
            user=self.user,
            course_id=self.course_key
        )
        return {UsageKey.from_string(mod.content_id).map_into_course(self.course_key) for mod in modules}

    # Serialization properties

    @lazy
    def user(self):
        """
        Return the StudentProgress user
        """
        return self._inner.user

    @lazy
    def course_key(self):
        """
        Return the StudentProgress course_key
        """
        return self._inner.course_id

    @lazy
    def chapter(self):
        """
        Return a list of BlockCompletions for each chapter in the course.
        """
        return self.get_completions_in_category('chapter')

    @lazy
    def sequential(self):
        """
        Return a list of BlockCompletions for each sequential in the course.
        """
        return self.get_completions_in_category('sequential')

    @lazy
    def vertical(self):
        """
        Return a list of BlockCompletions for each vertical in the course.
        """
        return self.get_completions_in_category('vertical')

    @property
    def mean(self):
        """
        Return the mean completion ratio for all enrolled users.
        """
        mean_cache_key = self.MEAN_CACHE_KEY_FORMAT.format(course_key=self.course_key)
        mean = cache.get(mean_cache_key)
        if mean is None:
            excluded_users = get_aggregate_exclusion_user_ids(self.course_key)
            mean = _get_course_progress_metrics(self.course_key, exclude_users=excluded_users)['course_avg']
            cache.set(mean_cache_key, mean, 1800)  # Cache for 30 minutes
        return mean / 100.0


class BlockCompletion(CompletionDataMixin, object):
    """
    Class to represent completed blocks within a given block of the course.
    """

    def __init__(self, user, block_key, course_completion):
        self.user = user
        self.block_key = block_key
        self.course_key = block_key.course_key
        self.course_completion = course_completion
        self._completed_blocks = None

    @lazy
    def stats(self):
        """
        Return a dictionary mapping all aggregate nodes to their
        completion statistics.
        """
        return self.course_completion.all_stats[self.block_key]


class _Stats(object):
    """
    A data object to track completion at a given block level.

    _Stats objects can be combined through simple addition.
    """

    @classmethod
    def empty(cls):
        """
        Create and return an empty _Stats object
        """
        return cls(0, 0)

    def __init__(self, earned, possible):
        self.earned = earned
        self.possible = possible

    def __add__(self, other):
        return _Stats(
            earned=self.earned + other.earned,
            possible=self.possible + other.possible,
        )
