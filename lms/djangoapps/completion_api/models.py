"""
Model code for completion API, including django models and facade classes
wrapping progress extension models.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import itertools

from opaque_keys.edx.keys import UsageKey

from lms.djangoapps.course_blocks.api import get_course_blocks
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from progress.models import CourseModuleCompletion


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
    Common calculations for completion values of courses or blocks within courses.

    Classes using this mixin must implement:

        * self.earned (float)
        * self.blocks (BlockStructureBlockData)
    """

    _completable_blocks = None

    def _recurse_completable_blocks(self, block):
        """
        Return a list of all completable blocks within the subtree under `block`.
        """
        if block.block_type in IGNORE_CATEGORIES:
            return []
        elif block.block_type in AGGREGATE_CATEGORIES:
            return list(itertools.chain(
                *[self._recurse_completable_blocks(child)
                  for child in self.blocks.get_children(block)]
            ))
        else:
            return [block]

    @property
    def completable_blocks(self):
        """
        Return a list of UsageKeys for all blocks that can be completed that are
        visible to self.user.

        This method encapsulates the facade's access to the modulestore, making
        it a useful candidate for mocking.

        In case the course structure is a DAG, nodes with multiple parents will
        be represented multiple times in the list.
        """
        if self._completable_blocks is None:
            self._completable_blocks = self._recurse_completable_blocks(self.blocks.root_block_usage_key)
        return self._completable_blocks

    @property
    def possible(self):
        """
        Return the maximum number of completions the user could earn in the
        course.
        """
        return float(len(self.completable_blocks))

    @property
    def ratio(self):
        """
        Return the fraction of the course completed by the user.

        Ratio is returned as a float in the range [0.0, 1.0].
        """
        if self.possible == 0:
            ratio = 1.0
        else:
            ratio = self.earned / self.possible
        return ratio


class CourseCompletionFacade(CompletionDataMixin, object):
    """
    Facade wrapping progress.models.StudentProgress model.
    """

    _blocks = None
    _collected = None
    _completed_modules = None

    def __init__(self, inner):
        self._inner = inner
        self._completions_in_category = {}

    @property
    def collected(self):
        """
        Return the collected block structure for this course
        """
        if self._collected is None:
            self._collected = get_course_in_cache(self.course_key)
        return self._collected

    @property
    def blocks(self):
        """
        Return an
        `openedx.core.lib.block_structure.block_structure.BlockStructureBlockData`
        collection which behaves as dict that maps
        `opaque_keys.edx.locator.BlockUsageLocator`s to
        `openedx.core.lib.block_structure.block_structure.BlockData` objects
        for all blocks in the course.
        """
        if self._blocks is None:
            course_location = CourseOverview.load_from_module_store(self.course_key).location
            self._blocks = get_course_blocks(
                self.user,
                course_location,
                collected_block_structure=self.collected,
            )
        return self._blocks

    @property
    def user(self):
        """
        Return the StudentProgress user
        """
        return self._inner.user

    @property
    def course_key(self):
        """
        Return the StudentProgress course_key
        """
        return self._inner.course_id

    @property
    def earned(self):
        """
        Return the number of completions earned by the user.
        """
        return self._inner.completions

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

    @property
    def completed_modules(self):
        """
        Returns a list of usage keys for modules that have been completed.
        """
        if self._completed_modules is None:
            modules = CourseModuleCompletion.objects.filter(
                user=self.user,
                course_id=self.course_key
            )
            self._completed_modules = {
                UsageKey.from_string(mod.content_id).map_into_course(self.course_key)
                for mod in modules
            }
        return self._completed_modules

    @property
    def chapter(self):
        """
        Return a list of BlockCompletions for each chapter in the course.
        """
        return self.get_completions_in_category('chapter')

    @property
    def sequential(self):
        """
        Return a list of BlockCompletions for each sequential in the course.
        """
        return self.get_completions_in_category('sequential')

    @property
    def vertical(self):
        """
        Return a list of BlockCompletions for each vertical in the course.
        """
        return self.get_completions_in_category('vertical')


class BlockCompletion(CompletionDataMixin, object):
    """
    Class to represent completed blocks within a given block of the course.
    """

    def __init__(self, user, block_key, course_completion):
        self.user = user
        self.block_key = block_key
        self.course_key = block_key.course_key
        self.course_completion = course_completion
        self._blocks = None
        self._completable_blocks = None
        self._completed_blocks = None

    @property
    def blocks(self):
        """
        Return an `openedx.core.lib.block_structure.block_structure.BlockStructureBlockData`
        object which behaves as dict that maps `opaque_keys.edx.locator.BlockUsageLocator`s
        to `openedx.core.lib.block_structure.block_structure.BlockData` objects
        for all blocks in the sub-tree (or DAG) under self.block_key.
        """
        if self._blocks is None:

            self._blocks = get_course_blocks(
                self.user,
                self.block_key,
                collected_block_structure=self.course_completion.collected,
            )
        return self._blocks

    @property
    def completed_blocks(self):
        """
        Return the list of UsageKeys of all blocks within self.block that have been
        completed by self.user.
        """
        if self._completed_blocks is None:
            modules = self.course_completion.completed_modules
            self._completed_blocks = [blk for blk in self.completable_blocks if blk in modules]
        return self._completed_blocks

    @property
    def earned(self):
        """
        The number of earned completions within self.block.
        """
        return float(len(self.completed_blocks))
