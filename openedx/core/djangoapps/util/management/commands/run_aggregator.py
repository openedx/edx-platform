# -*- coding: utf-8 -*-
"""
Performance tests for completion aggregator.
"""

import datetime
import math
import random
from timeit import default_timer

import pytz
from completion.models import BlockCompletion
from django.core.management.base import BaseCommand, CommandError
import numpy
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import SignalHandler, modulestore

COURSE_TREE_BREADTH = [3, 3, 3, 3]
STUDENTS_COUNT = 2
BLOCK_COMPLETIONS_COUNT = 30


class Command(BaseCommand):
    """ Run performance tests for completion aggregator. """

    help = "Run performance tests for completion aggregator."

    def add_arguments(self, parser):
        parser.add_argument(
            'test',
            help='Test to run.'
        )

    def handle(self, *args, **options):
        test = options.get('test')

        if not hasattr(self, test):
            raise CommandError('%s not found.' % test)

        self.setUp()
        getattr(self, test)()

    def setUp(self):
        """ Set up the course and users. """

        self.timer = default_timer
        self.store = modulestore()
        self.blocks = []

        with self.store.default_store(ModuleStoreEnum.Type.split):
            fields = {'display_name': 'Course', 'start': datetime.datetime(2015, 1, 1, 1, tzinfo=pytz.utc)}
            self.course = modulestore().create_course(
                'completion',
                '101',
                unicode(random.randint(1, 9999)),
                ModuleStoreEnum.UserID.test,
                fields=fields
            )

            with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
                with self.store.bulk_operations(self.course.id):
                    for __ in range(COURSE_TREE_BREADTH[0]):
                        chapter = self._create_block(parent=self.course, category='chapter')
                        for __ in range(COURSE_TREE_BREADTH[1]):
                            sequence = self._create_block(parent=chapter, category='sequential')
                            for __ in range(COURSE_TREE_BREADTH[2]):
                                vertical = self._create_block(parent=sequence, category='vertical')
                                self.blocks += [
                                    self._create_block(
                                        parent=vertical, category='html'
                                    ) for __ in range(COURSE_TREE_BREADTH[3])
                                ]
                                self.store.publish(vertical.location, ModuleStoreEnum.UserID.test)

            self.course = self.store.get_course(self.course.id)

        self.users = [UserFactory.create() for __ in range(STUDENTS_COUNT)]
        for user in self.users:
            CourseEnrollmentFactory(user=user, course_id=self.course.id)

    def _create_block(self, parent, category):
        fields = {'display_name': category, 'start': datetime.datetime(2015, 1, 1, 1, tzinfo=pytz.utc)}
        return self.store.create_child(ModuleStoreEnum.UserID.test, parent.location, category, fields=fields)

    def _print_results_header(self, test_name, time_taken=None):
        """ Print header. """
        print u"\n"
        print u"----- Completion Aggregator Performance Test Results -----"
        print u"Test: {}".format(test_name)
        print u"Course: {}".format(self.course.id)
        print u"Course Breadth: {}".format(COURSE_TREE_BREADTH)
        print u"Students: {}".format(STUDENTS_COUNT)
        if time_taken:
            print u"Total task time: {:.2f}ms".format(time_taken)

    def _print_results_footer(self):
        """ Print footer. """
        print u"----------------------------------------------------------"

    def _update_aggregators(self, username, course_key, block_keys=(), force=False):
        from completion_aggregator.tasks import update_aggregators
        update_aggregators(username, course_key, block_keys=block_keys, force=force)

    def _complete_blocks_for_users(self, blocks, users):
        for user in users:
            for block in blocks:
                BlockCompletion.objects.submit_completion(
                    user=user,
                    course_key=self.course.id,
                    block_key=block.location,
                    completion=1.0
                )
                self._update_aggregators(user.username, unicode(self.course.id), block_keys=[unicode(block.location)])

    def _assert_vertical_completion_for_all_users(self, vertical, expected_completion):
        from completion_aggregator.models import Aggregator
        for user in self.users:
            vertical_completion = Aggregator.objects.get(
                user=user, course_key=self.course.id, block_key=vertical.location
            ).percent
            assert abs(vertical_completion - expected_completion) < 0.01

    def _time_handler(self, handler, **kwargs):
        """ Time how long it takes to run handler. """
        timer_start = self.timer()
        handler(**kwargs)
        timer_end = self.timer()
        return (timer_end - timer_start) * 1000

    def test_course_published_handler_when_block_is_added(self):

        # Other listeners are connected so we time the handler alone later.
        from completion_aggregator.signals import course_published_handler
        SignalHandler.course_published.disconnect(course_published_handler)

        vertical = self.course.get_children()[-1].get_children()[-1].get_children()[-1]
        self._complete_blocks_for_users(vertical.get_children(), self.users)
        self._assert_vertical_completion_for_all_users(vertical, 1.0)
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            with self.store.bulk_operations(self.course.id):
                self._create_block(parent=vertical, category='html')
                self.store.publish(vertical.location, ModuleStoreEnum.UserID.test)
        time_taken = self._time_handler(course_published_handler, course_key=self.course.id)
        self._print_results_header(u"test_course_published_handler_when_block_is_added", time_taken=time_taken)
        self._assert_vertical_completion_for_all_users(
            vertical, COURSE_TREE_BREADTH[3] / (COURSE_TREE_BREADTH[3] + 1.0)
        )
        self._print_results_footer()

    def test_item_deleted_handler_when_block_is_deleted(self):

        # Other listeners are connected so we time the handler alone later.
        from completion_aggregator.signals import item_deleted_handler
        SignalHandler.course_published.disconnect(item_deleted_handler)

        vertical = self.course.get_children()[-1].get_children()[-1].get_children()[-1]
        self._complete_blocks_for_users(vertical.get_children()[1:], self.users)
        self._assert_vertical_completion_for_all_users(
            vertical, (COURSE_TREE_BREADTH[3] - 1.0) / COURSE_TREE_BREADTH[3]
        )
        block = vertical.get_children()[0]
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.delete_item(block.location, ModuleStoreEnum.UserID.test)
        time_taken = self._time_handler(item_deleted_handler, usage_key=block.location, user_id=None)
        self._print_results_header(u"test_item_deleted_handler_when_block_is_deleted", time_taken=time_taken)
        self._assert_vertical_completion_for_all_users(vertical, 1.0)
        self._print_results_footer()

    def test_individual_block_completions(self):

        from completion_aggregator.models import Aggregator

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
            self._complete_blocks_for_users([next_block], [random_user])
            timer_end = self.timer()
            elapsed_milliseconds = (timer_end - timer_start) * 1000
            times_taken.append(elapsed_milliseconds)

        for user in self.users:
            expected_verticals_completed = math.floor(user.next_block_index_to_complete / COURSE_TREE_BREADTH[3])
            verticals_completed = Aggregator.objects.filter(
                user=user, course_key=self.course.id, aggregation_name='vertical', percent=1.0
            ).count()
            assert expected_verticals_completed == verticals_completed

        time_sum = numpy.sum(times_taken)
        time_average = (time_sum / BLOCK_COMPLETIONS_COUNT)
        time_percentiles = " | ".join(
            [u"{}%: {:.2f}ms".format(p, numpy.percentile(times_taken, p)) for p in [
                50, 66, 75, 80, 90, 95, 98, 99, 100]
             ]
        )

        self._print_results_header(u"test_individual_block_completions")
        print u"Block Completions: {}".format(BLOCK_COMPLETIONS_COUNT)
        print u"Total time: {:.2f}ms".format(time_sum)
        print u"Average time: {:.2f}ms".format(time_average)
        print u"Time Percentiles: {}".format(time_percentiles)
        self._print_results_footer()
