from __future__ import absolute_import, division, print_function, unicode_literals

import sys
from itertools import chain
from unittest import skip

from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient

from completion_aggregator.models import Aggregator

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.models import CourseEnrollment
from student.tests.factories import AdminFactory, UserFactory


class AggregationRequestTestCase(SharedModuleStoreTestCase):
    chapter_count = 8  # 8
    sequential_count = 3  # 8 * 3 = 24
    vertical_count = 12  # 8 * 3 * 12 = 288
    block_count = 5  # 8 * 3 * 12 * 5 = 1440
    user_count = 50000
    page_size = 10000

    @classmethod
    def setUpClass(cls):
        super(AggregationRequestTestCase, cls).setUpClass()
        cls.chapters = []
        cls.sequentials = []
        cls.verticals = []
        cls.blocks = []
        print("CREATING COURSE", timezone.now())
        cls.course = CourseFactory.create()
        with cls.store.bulk_operations(cls.course.id):
            for _ in range(cls.chapter_count):
                chapter = ItemFactory.create(
                    parent=cls.course,
                    category="chapter",
                )
                cls.chapters.append(chapter)
                for _ in range(cls.sequential_count):
                    sequential = ItemFactory.create(
                        parent=chapter,
                        category='sequential',
                    )
                    cls.sequentials.append(sequential)
                    for _ in range(cls.vertical_count):
                        vertical = ItemFactory.create(
                            parent=sequential,
                            category="vertical",
                        )
                        cls.verticals.append(vertical)
                        for _ in range(cls.block_count):
                            block = ItemFactory.create(
                                parent=vertical,
                                category='html'
                            )
                            cls.blocks.append(block)
        for block in chain([cls.course], cls.chapters, cls.sequentials, cls.verticals, cls.blocks):
            block.mapped_location = block.location.map_into_course(cls.course.id)

    @skip("This test's setup takes too long for regular use")
    def test_full_query_no_completions(self):
        start = timezone.now()
        client = APIClient()
        print("CREATING USERS", timezone.now())
        admin = AdminFactory.create(username='admin', password='admin')
        users = []
        one_percent = self.user_count / 100
        for i in range(self.user_count):
            users.append(User(username='user{}'.format(i)))
            if i % one_percent == one_percent - 1:
                print('.', end='')
                sys.stdout.flush()
            #users.append(UserFactory.create())
        User.objects.bulk_create(users)
        print("CREATING ENROLLMENTS AND AGGREGATORS", timezone.now())
        enrollments = []
        aggs = []
        for i, user in enumerate(users):
            if i % one_percent == one_percent - 1:
                print('.', end='')
                sys.stdout.flush()
            enrollments.append(
                CourseEnrollment(user=user, course_id=self.course.id)
            )
            aggs.append(
                Aggregator(
                    user=user,
                    course_key=self.course.id,
                    block_key=self.course.mapped_location,
                    aggregation_name='course',
                    earned=576.0,
                    possible=1044.0,
                    percent=0.4,
                    last_modified=start,
                )
            )
            for chapter in self.chapters:
                aggs.append(
                    Aggregator(
                        user=user,
                        course_key=self.course.id,
                        block_key=chapter.mapped_location,
                        aggregation_name='chapter',
                        earned=72.0,
                        possible=180.0,
                        percent=0.4,
                        last_modified=start,
                    )
                )
            continue
            for sequential in self.sequentials:
                aggs.append(
                    Aggregator(
                        user=user,
                        course_key=self.course.id,
                        block_key=sequential.mapped_location,
                        aggregation_name='sequential',
                        earned=24.0,
                        possible=60.0,
                        percent=0.4,
                        last_modified=start,
                    )
                )
            for vertical in self.verticals:
                aggs.append(
                    Aggregator(
                        user=user,
                        course_key=self.course.id,
                        block_key=vertical.mapped_location,
                        aggregation_name='vertical',
                        earned=2.0,
                        possible=5.0,
                        percent=0.4,
                        last_modified=start,
                    )
                )
        print("Enrollments:", len(enrollments))
        print("Aggregators:", len(aggs))
        CourseEnrollment.objects.bulk_create(enrollments, batch_size=500)
        Aggregator.objects.bulk_create(aggs, batch_size=500)
        client.login(username='admin', password='admin')
        startquery = timezone.now()
        print("START", startquery)
        results = []

        url = '/api/completion-aggregator/v1/course/{}/?page_size={}&requested_fields=chapter'.format(self.course.id, self.page_size)
        url = '/api/completion-aggregator/v1/course/{}/?page_size={}'.format(self.course.id, self.page_size)
        response = client.get(url)
        self.assertEqual(len(response.data['results']), self.page_size)
        results.extend(response.data['results'])
        print(connection.queries)
        print("  ", response.data['pagination'], timezone.now())
        while response.data['pagination']['next']:
            response = client.get(response.data['pagination']['next'])
            print("  ", response.data['pagination'], timezone.now())
            results.extend(response.data['results'])
        endquery = timezone.now()
        print('End collection', endquery)
        self.assertEqual(len(results), self.user_count)
        print("Query run time: {}s".format((endquery - startquery).total_seconds()))
        print(results[:10])
        self.assertLess(endquery - startquery, timedelta(seconds=128))
        self.assertLess(endquery - startquery, timedelta(seconds=64))
        self.assertLess(endquery - startquery, timedelta(seconds=32))
        self.assertLess(endquery - startquery, timedelta(seconds=16))
        self.assertLess(endquery - startquery, timedelta(seconds=8))
