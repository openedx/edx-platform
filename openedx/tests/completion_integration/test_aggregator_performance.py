"""
Tests of completion xblock runtime services
"""
import math
import random
from timeit import default_timer
import unittest

from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
import numpy
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

COURSE_TREE_BREADTH = [3, 3, 3, 3]
STUDENTS_COUNT = 2
BLOCK_COMPLETIONS_COUNT = 30


@unittest.skip
class AggregatorPerformanceTestCase(CompletionWaffleTestMixin, ModuleStoreTestCase):
    """
    Tests for calculating performance of completion_aggregator.

    To test:
    1. Remove skip.
    2. Set constants at top of file.
    3. pytest <file-path>::AggregatorPerformanceTestCase -k <test-name> --capture=no
    """

    ENABLED_SIGNALS = ['course_published', 'item_deleted']

    def setUp(self):
        super(AggregatorPerformanceTestCase, self).setUp()

        self.timer = default_timer

        self.override_waffle_switch(True)
        self.course = CourseFactory.create()

        self.users = [UserFactory.create() for __ in range(STUDENTS_COUNT)]
        for user in self.users:
            CourseEnrollmentFactory(user=user, course_id=self.course.id)

        self.blocks = []

        with self.store.bulk_operations(self.course.id):

            for __ in range(COURSE_TREE_BREADTH[0]):
                chapter = ItemFactory.create(parent=self.course, category='chapter')
                for __ in range(COURSE_TREE_BREADTH[1]):
                    sequence = ItemFactory.create(parent=chapter, category='sequential')
                    for __ in range(COURSE_TREE_BREADTH[2]):
                        vertical = ItemFactory.create(parent=sequence, category='vertical')
                        self.blocks += [
                            ItemFactory.create(parent=vertical, category='html') for __ in range(COURSE_TREE_BREADTH[3])
                        ]

    def print_results_header(self, test_name):
        """ Print header. """
        print u"\n"
        print u"----- Completion Aggregator Performance Test Results -----"
        print u"Test: {}".format(test_name)
        print u"Chapters: {} Sequentials per Chapter: {} Verticals per Sequential : {} Blocks per Vertical: {}".format(
            *COURSE_TREE_BREADTH
        )
        print u"Students: {}".format(STUDENTS_COUNT)

    def print_results_footer(self):
        """ Print footer. """
        print u"----------------------------------------------------------"

    def complete_blocks_for_all_users(self, blocks):
        for user in self.users:
            for block in blocks:
                BlockCompletion.objects.submit_completion(
                    user=user,
                    course_key=self.course.id,
                    block_key=block.location,
                    completion=1.0
                )

    def assert_vertical_completion_for_all_users(self, vertical, expected_completion):
        from completion_aggregator.models import Aggregator
        for user in self.users:
            vertical_completion = Aggregator.objects.get(
                user=user, course_key=self.course.id, block_key=vertical.location
            ).percent
            self.assertEqual(vertical_completion, expected_completion)

    def time_handler(self, handler, **kwargs):
        """ Time how long it takes to run handler. """
        timer_start = self.timer()
        handler(**kwargs)
        timer_end = self.timer()
        elapsed_milliseconds = (timer_end - timer_start) * 1000
        print u"Total task time: {:.2f}ms".format(elapsed_milliseconds)

    def test_course_published_handler_when_block_is_added(self):

        from completion_aggregator.signals import course_published_handler

        self.print_results_header(u"test_course_published_handler_when_block_is_added")

        # Other listeners are connected so we time the handler alone later.
        SignalHandler.course_published.disconnect(course_published_handler)

        vertical = self.course.get_children()[-1].get_children()[-1].get_children()[-1]
        self.complete_blocks_for_all_users(vertical.get_children())
        self.assert_vertical_completion_for_all_users(vertical, 1.0)
        ItemFactory.create(parent=vertical, category='html')
        self.time_handler(course_published_handler, course_key=self.course.id)
        self.assert_vertical_completion_for_all_users(
            vertical, COURSE_TREE_BREADTH[3] / (COURSE_TREE_BREADTH[3] + 1.0)
        )
        self.print_results_footer()

    def test_item_deleted_handler_when_block_is_deleted(self):

        from completion_aggregator.signals import item_deleted_handler

        self.print_results_header(u"test_item_deleted_handler_when_block_is_deleted")

        # Other listeners are connected so we time the handler alone later.
        SignalHandler.item_deleted.disconnect(item_deleted_handler)

        vertical = self.course.get_children()[-1].get_children()[-1].get_children()[-1]
        self.complete_blocks_for_all_users(vertical.get_children()[1:])
        self.assert_vertical_completion_for_all_users(
            vertical, (COURSE_TREE_BREADTH[3] - 1.0) / COURSE_TREE_BREADTH[3]
        )
        block = vertical.get_children()[0]
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.delete_item(block.location, ModuleStoreEnum.UserID.test)
        self.time_handler(item_deleted_handler, usage_key=block.location, user_id=None)
        self.assert_vertical_completion_for_all_users(vertical, 1.0)
        self.print_results_footer()

    def test_individual_block_completions_performance(self):

        from completion_aggregator.models import Aggregator

        self.print_results_header(u"test_individual_block_completions_performance")

        times_taken = []

        for user in self.users:
            user.next_block_index_to_complete = 0

        users = list(self.users)

        for __ in range(BLOCK_COMPLETIONS_COUNT):
            random_user = random.choice(users)
            next_block = self.blocks[random_user.next_block_index_to_complete]
            random_user.next_block_index_to_complete += 1
            if random_user.next_block_index_to_complete >= len(self.blocks):
                users.remove(random_user)

            timer_start = self.timer()
            BlockCompletion.objects.submit_completion(
                user=random_user,
                course_key=self.course.id,
                block_key=next_block.location,
                completion=1.0
            )
            timer_end = self.timer()
            elapsed_milliseconds = (timer_end - timer_start) * 1000
            times_taken.append(elapsed_milliseconds)

        for user in self.users:
            expected_verticals_completed = math.floor(user.next_block_index_to_complete / COURSE_TREE_BREADTH[3])
            verticals_completed = Aggregator.objects.filter(
                user=user, course_key=self.course.id, aggregation_name='vertical', percent=1.0
            ).count()
            self.assertEqual(expected_verticals_completed, verticals_completed)

        time_sum = numpy.sum(times_taken)
        time_average = (time_sum / BLOCK_COMPLETIONS_COUNT)
        time_percentiles = " | ".join(
            [u"{}%: {:.2f}ms".format(p, numpy.percentile(times_taken, p)) for p in [
                50, 66, 75, 80, 90, 95, 98, 99, 100]
             ]
        )

        print u"Block Completions: {}".format(BLOCK_COMPLETIONS_COUNT)
        print u"Total time: {:.2f}ms".format(time_sum)
        print u"Average time: {:.2f}ms".format(time_average)
        print u"Time Percentiles: {}".format(time_percentiles)
        self.print_results_footer()
