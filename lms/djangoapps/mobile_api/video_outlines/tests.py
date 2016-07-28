# -*- coding: utf-8 -*-
"""
Tests for video outline API
"""

import itertools
from uuid import uuid4
from collections import namedtuple

import ddt
from nose.plugins.attrib import attr
from edxval import api
from milestones.tests.utils import MilestonesTestCaseMixin
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.video_module import transcripts_utils
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import Group, UserPartition
from milestones.tests.utils import MilestonesTestCaseMixin

from mobile_api.models import MobileApiConfig
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.course_groups.models import CourseUserGroupPartitionGroup
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort, remove_user_from_cohort
from mobile_api.testutils import MobileAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin


class TestVideoAPITestCase(MobileAPITestCase):
    """
    Base test class for video related mobile APIs
    """
    def setUp(self):
        super(TestVideoAPITestCase, self).setUp()
        self.section = ItemFactory.create(
            parent=self.course,
            category="chapter",
            display_name=u"test factory section omega \u03a9",
        )
        self.sub_section = ItemFactory.create(
            parent=self.section,
            category="sequential",
            display_name=u"test subsection omega \u03a9",
        )

        self.unit = ItemFactory.create(
            parent=self.sub_section,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit omega \u03a9",
        )
        self.other_unit = ItemFactory.create(
            parent=self.sub_section,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit omega 2 \u03a9",
        )
        self.nameless_unit = ItemFactory.create(
            parent=self.sub_section,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=None,
        )

        self.edx_video_id = 'testing-123'
        self.video_url = 'http://val.edx.org/val/video.mp4'
        self.video_url_high = 'http://val.edx.org/val/video_high.mp4'
        self.youtube_url = 'http://val.edx.org/val/youtube.mp4'
        self.html5_video_url = 'http://video.edx.org/html5/video.mp4'

        api.create_profile('youtube')
        api.create_profile('mobile_high')
        api.create_profile('mobile_low')

        # create the video in VAL
        api.create_video({
            'edx_video_id': self.edx_video_id,
            'status': 'test',
            'client_video_id': u"test video omega \u03a9",
            'duration': 12,
            'courses': [unicode(self.course.id)],
            'encoded_videos': [
                {
                    'profile': 'youtube',
                    'url': 'xyz123',
                    'file_size': 0,
                    'bitrate': 1500
                },
                {
                    'profile': 'mobile_low',
                    'url': self.video_url,
                    'file_size': 12345,
                    'bitrate': 250
                },
                {
                    'profile': 'mobile_high',
                    'url': self.video_url_high,
                    'file_size': 99999,
                    'bitrate': 250
                },

            ]})

        # Set requested profiles
        MobileApiConfig(video_profiles="mobile_low,mobile_high,youtube").save()


class TestVideoAPIMixin(object):
    """
    Mixin class that provides helpers for testing video related mobile APIs
    """
    def _create_video_with_subs(self, custom_subid=None):
        """
        Creates and returns a video with stored subtitles.
        """
        subid = custom_subid or uuid4().hex
        transcripts_utils.save_subs_to_store(
            {
                'start': [100, 200, 240, 390, 1000],
                'end': [200, 240, 380, 1000, 1500],
                'text': [
                    'subs #1',
                    'subs #2',
                    'subs #3',
                    'subs #4',
                    'subs #5'
                ]
            },
            subid,
            self.course)
        return ItemFactory.create(
            parent=self.unit,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"test video omega \u03a9",
            sub=subid
        )

    def _verify_paths(self, course_outline, path_list, outline_index=0):
        """
        Takes a path_list and compares it against the course_outline

        Attributes:
            course_outline (list): A list of dictionaries that includes a 'path'
                and 'named_path' field which we will be comparing path_list to
            path_list (list): A list of the expected strings
            outline_index (int): Index into the course_outline list for which the
                path is being tested.
        """
        path = course_outline[outline_index]['path']
        self.assertEqual(len(path), len(path_list))
        for i in range(len(path_list)):
            self.assertEqual(path_list[i], path[i]['name'])
        #named_path will be deprecated eventually
        named_path = course_outline[outline_index]['named_path']
        self.assertEqual(len(named_path), len(path_list))
        for i in range(len(path_list)):
            self.assertEqual(path_list[i], named_path[i])

    def _setup_course_partitions(self, scheme_id='random', is_cohorted=False):
        """Helper method to configure the user partitions in the course."""
        self.partition_id = 0  # pylint: disable=attribute-defined-outside-init
        self.course.user_partitions = [
            UserPartition(
                self.partition_id, 'first_partition', 'First Partition',
                [Group(0, 'alpha'), Group(1, 'beta')],
                scheme=None, scheme_id=scheme_id
            ),
        ]
        self.course.cohort_config = {'cohorted': is_cohorted}
        self.store.update_item(self.course, self.user.id)

    def _setup_group_access(self, xblock, partition_id, group_ids):
        """Helper method to configure the partition and group mapping for the given xblock."""
        xblock.group_access = {partition_id: group_ids}
        self.store.update_item(xblock, self.user.id)

    def _setup_split_module(self, sub_block_category):
        """Helper method to configure a split_test unit with children of type sub_block_category."""
        self._setup_course_partitions()
        self.split_test = ItemFactory.create(  # pylint: disable=attribute-defined-outside-init
            parent=self.unit,
            category="split_test",
            display_name=u"split test unit",
            user_partition_id=0,
        )
        sub_block_a = ItemFactory.create(
            parent=self.split_test,
            category=sub_block_category,
            display_name=u"split test block a",
        )
        sub_block_b = ItemFactory.create(
            parent=self.split_test,
            category=sub_block_category,
            display_name=u"split test block b",
        )
        self.split_test.group_id_to_child = {
            str(index): url for index, url in enumerate([sub_block_a.location, sub_block_b.location])
        }
        self.store.update_item(self.split_test, self.user.id)
        return sub_block_a, sub_block_b


@attr('shard_2')
class TestNonStandardCourseStructure(MobileAPITestCase, TestVideoAPIMixin, MilestonesTestCaseMixin):
    """
    Tests /api/mobile/v0.5/video_outlines/courses/{course_id} with no course set
    """
    REVERSE_INFO = {'name': 'video-summary-list', 'params': ['course_id']}

    def setUp(self):
        super(TestNonStandardCourseStructure, self).setUp()
        self.chapter_under_course = ItemFactory.create(
            parent=self.course,
            category="chapter",
            display_name=u"test factory chapter under course omega \u03a9",
        )
        self.section_under_course = ItemFactory.create(
            parent=self.course,
            category="sequential",
            display_name=u"test factory section under course omega \u03a9",
        )
        self.section_under_chapter = ItemFactory.create(
            parent=self.chapter_under_course,
            category="sequential",
            display_name=u"test factory section under chapter omega \u03a9",
        )
        self.vertical_under_course = ItemFactory.create(
            parent=self.course,
            category="vertical",
            display_name=u"test factory vertical under course omega \u03a9",
        )
        self.vertical_under_section = ItemFactory.create(
            parent=self.section_under_chapter,
            category="vertical",
            display_name=u"test factory vertical under section omega \u03a9",
        )

    def test_structure_course_video(self):
        """
        Tests when there is a video without a vertical directly under course
        """
        self.login_and_enroll()
        ItemFactory.create(
            parent=self.course,
            category="video",
            display_name=u"test factory video omega \u03a9",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertRegexpMatches(section_url, r'courseware$')
        self.assertEqual(section_url, unit_url)

        self._verify_paths(course_outline, [])

    def test_structure_course_vert_video(self):
        """
        Tests when there is a video under vertical directly under course
        """
        self.login_and_enroll()
        ItemFactory.create(
            parent=self.vertical_under_course,
            category="video",
            display_name=u"test factory video omega \u03a9",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertRegexpMatches(
            section_url,
            r'courseware/test_factory_vertical_under_course_omega_%CE%A9/$'
        )
        self.assertEqual(section_url, unit_url)

        self._verify_paths(
            course_outline,
            [
                u'test factory vertical under course omega \u03a9'
            ]
        )

    def test_structure_course_chap_video(self):
        """
        Tests when there is a video directly under chapter
        """
        self.login_and_enroll()

        ItemFactory.create(
            parent=self.chapter_under_course,
            category="video",
            display_name=u"test factory video omega \u03a9",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertRegexpMatches(
            section_url,
            r'courseware/test_factory_chapter_under_course_omega_%CE%A9/$'
        )

        self.assertEqual(section_url, unit_url)

        self._verify_paths(
            course_outline,
            [
                u'test factory chapter under course omega \u03a9',
            ]
        )

    def test_structure_course_section_video(self):
        """
        Tests when chapter is none, and video under section under course
        """
        self.login_and_enroll()
        ItemFactory.create(
            parent=self.section_under_course,
            category="video",
            display_name=u"test factory video omega \u03a9",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertRegexpMatches(
            section_url,
            r'courseware/test_factory_section_under_course_omega_%CE%A9/$'
        )

        self.assertEqual(section_url, unit_url)

        self._verify_paths(
            course_outline,
            [
                u'test factory section under course omega \u03a9',
            ]
        )

    def test_structure_course_chap_section_video(self):
        """
        Tests when chapter and sequential exists, with a video with no vertical.
        """
        self.login_and_enroll()

        ItemFactory.create(
            parent=self.section_under_chapter,
            category="video",
            display_name=u"meow factory video omega \u03a9",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertRegexpMatches(
            section_url,
            (
                r'courseware/test_factory_chapter_under_course_omega_%CE%A9/' +
                'test_factory_section_under_chapter_omega_%CE%A9/$'
            )
        )

        self.assertEqual(section_url, unit_url)

        self._verify_paths(
            course_outline,
            [
                u'test factory chapter under course omega \u03a9',
                u'test factory section under chapter omega \u03a9',
            ]
        )

    def test_structure_course_section_vert_video(self):
        """
        Tests chapter->section->vertical->unit
        """
        self.login_and_enroll()
        ItemFactory.create(
            parent=self.vertical_under_section,
            category="video",
            display_name=u"test factory video omega \u03a9",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertRegexpMatches(
            section_url,
            (
                r'courseware/test_factory_chapter_under_course_omega_%CE%A9/' +
                'test_factory_section_under_chapter_omega_%CE%A9/$'
            )
        )
        self.assertRegexpMatches(
            unit_url,
            (
                r'courseware/test_factory_chapter_under_course_omega_%CE%A9/' +
                'test_factory_section_under_chapter_omega_%CE%A9/1$'
            )
        )

        self._verify_paths(
            course_outline,
            [
                u'test factory chapter under course omega \u03a9',
                u'test factory section under chapter omega \u03a9',
                u'test factory vertical under section omega \u03a9'
            ]
        )


@attr('shard_2')
@ddt.ddt
class TestVideoSummaryList(TestVideoAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin,
                           TestVideoAPIMixin, MilestonesTestCaseMixin):
    """
    Tests for /api/mobile/v0.5/video_outlines/courses/{course_id}..
    """
    REVERSE_INFO = {'name': 'video-summary-list', 'params': ['course_id']}

    def test_only_on_web(self):
        self.login_and_enroll()

        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 0)

        subid = uuid4().hex
        transcripts_utils.save_subs_to_store(
            {
                'start': [100],
                'end': [200],
                'text': [
                    'subs #1',
                ]
            },
            subid,
            self.course)

        ItemFactory.create(
            parent=self.unit,
            category="video",
            display_name=u"test video",
            only_on_web=True,
            subid=subid
        )

        course_outline = self.api_response().data

        self.assertEqual(len(course_outline), 1)

        self.assertIsNone(course_outline[0]["summary"]["video_url"])
        self.assertIsNone(course_outline[0]["summary"]["video_thumbnail_url"])
        self.assertEqual(course_outline[0]["summary"]["duration"], 0)
        self.assertEqual(course_outline[0]["summary"]["size"], 0)
        self.assertEqual(course_outline[0]["summary"]["name"], "test video")
        self.assertEqual(course_outline[0]["summary"]["transcripts"], {})
        self.assertIsNone(course_outline[0]["summary"]["language"])
        self.assertEqual(course_outline[0]["summary"]["category"], "video")
        self.assertTrue(course_outline[0]["summary"]["only_on_web"])

    def test_mobile_api_config(self):
        """
        Tests VideoSummaryList with different MobileApiConfig video_profiles
        """
        self.login_and_enroll()
        edx_video_id = "testing_mobile_high"
        api.create_video({
            'edx_video_id': edx_video_id,
            'status': 'test',
            'client_video_id': u"test video omega \u03a9",
            'duration': 12,
            'courses': [unicode(self.course.id)],
            'encoded_videos': [
                {
                    'profile': 'youtube',
                    'url': self.youtube_url,
                    'file_size': 2222,
                    'bitrate': 4444
                },
                {
                    'profile': 'mobile_high',
                    'url': self.video_url_high,
                    'file_size': 111,
                    'bitrate': 333
                },

            ]})
        ItemFactory.create(
            parent=self.other_unit,
            category="video",
            display_name=u"testing mobile high video",
            edx_video_id=edx_video_id,
        )

        expected_output = {
            'category': u'video',
            'video_thumbnail_url': None,
            'language': u'en',
            'name': u'testing mobile high video',
            'video_url': self.video_url_high,
            'duration': 12.0,
            'transcripts': {
                'en': 'http://testserver/api/mobile/v0.5/video_outlines/transcripts/{}/testing_mobile_high_video/en'.format(self.course.id)  # pylint: disable=line-too-long
            },
            'only_on_web': False,
            'encoded_videos': {
                u'mobile_high': {
                    'url': self.video_url_high,
                    'file_size': 111
                },
                u'youtube': {
                    'url': self.youtube_url,
                    'file_size': 2222
                }
            },
            'size': 111
        }

        # Testing when video_profiles='mobile_low,mobile_high,youtube'
        course_outline = self.api_response().data
        course_outline[0]['summary'].pop("id")
        self.assertEqual(course_outline[0]['summary'], expected_output)

        # Testing when there is no mobile_low, and that mobile_high doesn't show
        MobileApiConfig(video_profiles="mobile_low,youtube").save()

        course_outline = self.api_response().data

        expected_output['encoded_videos'].pop('mobile_high')
        expected_output['video_url'] = self.youtube_url
        expected_output['size'] = 2222

        course_outline[0]['summary'].pop("id")
        self.assertEqual(course_outline[0]['summary'], expected_output)

        # Testing where youtube is the default video over mobile_high
        MobileApiConfig(video_profiles="youtube,mobile_high").save()

        course_outline = self.api_response().data

        expected_output['encoded_videos']['mobile_high'] = {
            'url': self.video_url_high,
            'file_size': 111
        }

        course_outline[0]['summary'].pop("id")
        self.assertEqual(course_outline[0]['summary'], expected_output)

    def test_video_not_in_val(self):
        self.login_and_enroll()
        self._create_video_with_subs()
        ItemFactory.create(
            parent=self.other_unit,
            category="video",
            edx_video_id="some_non_existent_id_in_val",
            display_name=u"some non existent video in val",
            html5_sources=[self.html5_video_url]
        )

        summary = self.api_response().data[1]['summary']
        self.assertEqual(summary['name'], "some non existent video in val")
        self.assertIsNone(summary['encoded_videos'])
        self.assertIsNone(summary['duration'])
        self.assertEqual(summary['size'], 0)
        self.assertEqual(summary['video_url'], self.html5_video_url)

    def test_course_list(self):
        self.login_and_enroll()
        self._create_video_with_subs()
        ItemFactory.create(
            parent=self.other_unit,
            category="video",
            display_name=u"test video omega 2 \u03a9",
            html5_sources=[self.html5_video_url]
        )
        ItemFactory.create(
            parent=self.other_unit,
            category="video",
            display_name=u"test video omega 3 \u03a9",
            source=self.html5_video_url
        )
        ItemFactory.create(
            parent=self.unit,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"test draft video omega \u03a9",
            visible_to_staff_only=True,
        )

        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 3)
        vid = course_outline[0]
        self.assertTrue('test_subsection_omega_%CE%A9' in vid['section_url'])
        self.assertTrue('test_subsection_omega_%CE%A9/1' in vid['unit_url'])
        self.assertTrue(u'test_video_omega_\u03a9' in vid['summary']['id'])
        self.assertEqual(vid['summary']['video_url'], self.video_url)
        self.assertEqual(vid['summary']['size'], 12345)
        self.assertTrue('en' in vid['summary']['transcripts'])
        self.assertFalse(vid['summary']['only_on_web'])
        self.assertEqual(course_outline[1]['summary']['video_url'], self.html5_video_url)
        self.assertEqual(course_outline[1]['summary']['size'], 0)
        self.assertFalse(course_outline[1]['summary']['only_on_web'])
        self.assertEqual(course_outline[1]['path'][2]['name'], self.other_unit.display_name)
        self.assertEqual(course_outline[1]['path'][2]['id'], unicode(self.other_unit.location))
        self.assertEqual(course_outline[2]['summary']['video_url'], self.html5_video_url)
        self.assertEqual(course_outline[2]['summary']['size'], 0)
        self.assertFalse(course_outline[2]['summary']['only_on_web'])

    def test_with_nameless_unit(self):
        self.login_and_enroll()
        ItemFactory.create(
            parent=self.nameless_unit,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"test draft video omega 2 \u03a9"
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        self.assertEqual(course_outline[0]['path'][2]['name'], self.nameless_unit.location.block_id)

    def test_with_video_in_sub_section(self):
        """
        Tests a non standard xml format where a video is underneath a sequential

        We are expecting to return the same unit and section url since there is
        no unit vertical.
        """
        self.login_and_enroll()
        ItemFactory.create(
            parent=self.sub_section,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"video in the sub section"
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 1)
        self.assertEqual(len(course_outline[0]['path']), 2)
        section_url = course_outline[0]["section_url"]
        unit_url = course_outline[0]["unit_url"]
        self.assertIn(
            u'courseware/test_factory_section_omega_%CE%A9/test_subsection_omega_%CE%A9',
            section_url

        )
        self.assertTrue(section_url)
        self.assertTrue(unit_url)
        self.assertEqual(section_url, unit_url)

    @ddt.data(
        *itertools.product([True, False], ["video", "problem"])
    )
    @ddt.unpack
    def test_with_split_block(self, is_user_staff, sub_block_category):
        """Test with split_module->sub_block_category and for both staff and non-staff users."""
        self.login_and_enroll()
        self.user.is_staff = is_user_staff
        self.user.save()
        self._setup_split_module(sub_block_category)

        video_outline = self.api_response().data
        num_video_blocks = 1 if sub_block_category == "video" else 0
        self.assertEqual(len(video_outline), num_video_blocks)
        for block_index in range(num_video_blocks):
            self._verify_paths(
                video_outline,
                [
                    self.section.display_name,
                    self.sub_section.display_name,
                    self.unit.display_name,
                    self.split_test.display_name
                ],
                block_index
            )
            self.assertIn(u"split test block", video_outline[block_index]["summary"]["name"])

    def test_with_split_vertical(self):
        """Test with split_module->vertical->video structure."""
        self.login_and_enroll()
        split_vertical_a, split_vertical_b = self._setup_split_module("vertical")

        ItemFactory.create(
            parent=split_vertical_a,
            category="video",
            display_name=u"video in vertical a",
        )
        ItemFactory.create(
            parent=split_vertical_b,
            category="video",
            display_name=u"video in vertical b",
        )

        video_outline = self.api_response().data

        # user should see only one of the videos (a or b).
        self.assertEqual(len(video_outline), 1)
        self.assertIn(u"video in vertical", video_outline[0]["summary"]["name"])
        a_or_b = video_outline[0]["summary"]["name"][-1:]
        self._verify_paths(
            video_outline,
            [
                self.section.display_name,
                self.sub_section.display_name,
                self.unit.display_name,
                self.split_test.display_name,
                u"split test block " + a_or_b
            ],
        )

    def _create_cohorted_video(self, group_id):
        """Creates a cohorted video block, giving access to only the given group_id."""
        video_block = ItemFactory.create(
            parent=self.unit,
            category="video",
            display_name=u"video for group " + unicode(group_id),
        )
        self._setup_group_access(video_block, self.partition_id, [group_id])

    def _create_cohorted_vertical_with_video(self, group_id):
        """Creates a cohorted vertical with a child video block, giving access to only the given group_id."""
        vertical_block = ItemFactory.create(
            parent=self.sub_section,
            category="vertical",
            display_name=u"vertical for group " + unicode(group_id),
        )
        self._setup_group_access(vertical_block, self.partition_id, [group_id])
        ItemFactory.create(
            parent=vertical_block,
            category="video",
            display_name=u"video for group " + unicode(group_id),
        )

    @ddt.data("_create_cohorted_video", "_create_cohorted_vertical_with_video")
    def test_with_cohorted_content(self, content_creator_method_name):
        self.login_and_enroll()
        self._setup_course_partitions(scheme_id='cohort', is_cohorted=True)

        cohorts = []
        for group_id in [0, 1]:
            getattr(self, content_creator_method_name)(group_id)

            cohorts.append(CohortFactory(course_id=self.course.id, name=u"Cohort " + unicode(group_id)))
            link = CourseUserGroupPartitionGroup(
                course_user_group=cohorts[group_id],
                partition_id=self.partition_id,
                group_id=group_id,
            )
            link.save()

        for cohort_index in range(len(cohorts)):
            # add user to this cohort
            add_user_to_cohort(cohorts[cohort_index], self.user.username)

            # should only see video for this cohort
            video_outline = self.api_response().data
            self.assertEqual(len(video_outline), 1)
            self.assertEquals(
                u"video for group " + unicode(cohort_index),
                video_outline[0]["summary"]["name"]
            )

            # remove user from this cohort
            remove_user_from_cohort(cohorts[cohort_index], self.user.username)

        # un-cohorted user should see no videos
        video_outline = self.api_response().data
        self.assertEqual(len(video_outline), 0)

        # staff user sees all videos
        self.user.is_staff = True
        self.user.save()
        video_outline = self.api_response().data
        self.assertEqual(len(video_outline), 2)

    def test_with_hidden_blocks(self):
        self.login_and_enroll()
        hidden_subsection = ItemFactory.create(
            parent=self.section,
            category="sequential",
            hide_from_toc=True,
        )
        unit_within_hidden_subsection = ItemFactory.create(
            parent=hidden_subsection,
            category="vertical",
        )
        hidden_unit = ItemFactory.create(
            parent=self.sub_section,
            category="vertical",
            hide_from_toc=True,
        )
        ItemFactory.create(
            parent=unit_within_hidden_subsection,
            category="video",
            edx_video_id=self.edx_video_id,
        )
        ItemFactory.create(
            parent=hidden_unit,
            category="video",
            edx_video_id=self.edx_video_id,
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 0)

    def test_language(self):
        self.login_and_enroll()
        video = ItemFactory.create(
            parent=self.nameless_unit,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"test draft video omega 2 \u03a9"
        )

        language_case = namedtuple('language_case', ['transcripts', 'expected_language'])
        language_cases = [
            # defaults to english
            language_case({}, "en"),
            # supports english
            language_case({"en": 1}, "en"),
            # supports another language
            language_case({"lang1": 1}, "lang1"),
            # returns first alphabetically-sorted language
            language_case({"lang1": 1, "en": 2}, "en"),
            language_case({"lang1": 1, "lang2": 2}, "lang1"),
        ]

        for case in language_cases:
            video.transcripts = case.transcripts
            modulestore().update_item(video, self.user.id)
            course_outline = self.api_response().data
            self.assertEqual(len(course_outline), 1)
            self.assertEqual(course_outline[0]['summary']['language'], case.expected_language)

    def test_transcripts(self):
        self.login_and_enroll()
        video = ItemFactory.create(
            parent=self.nameless_unit,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"test draft video omega 2 \u03a9"
        )

        transcript_case = namedtuple('transcript_case', ['transcripts', 'english_subtitle', 'expected_transcripts'])
        transcript_cases = [
            # defaults to english
            transcript_case({}, "", ["en"]),
            transcript_case({}, "en-sub", ["en"]),
            # supports english
            transcript_case({"en": 1}, "", ["en"]),
            transcript_case({"en": 1}, "en-sub", ["en"]),
            # keeps both english and other languages
            transcript_case({"lang1": 1, "en": 2}, "", ["lang1", "en"]),
            transcript_case({"lang1": 1, "en": 2}, "en-sub", ["lang1", "en"]),
            # adds english to list of languages only if english_subtitle is specified
            transcript_case({"lang1": 1, "lang2": 2}, "", ["lang1", "lang2"]),
            transcript_case({"lang1": 1, "lang2": 2}, "en-sub", ["lang1", "lang2", "en"]),
        ]

        for case in transcript_cases:
            video.transcripts = case.transcripts
            video.sub = case.english_subtitle
            modulestore().update_item(video, self.user.id)
            course_outline = self.api_response().data
            self.assertEqual(len(course_outline), 1)
            self.assertSetEqual(
                set(course_outline[0]['summary']['transcripts'].keys()),
                set(case.expected_transcripts)
            )


@attr('shard_2')
class TestTranscriptsDetail(TestVideoAPITestCase, MobileAuthTestMixin, MobileCourseAccessTestMixin,
                            TestVideoAPIMixin, MilestonesTestCaseMixin):
    """
    Tests for /api/mobile/v0.5/video_outlines/transcripts/{course_id}..
    """
    REVERSE_INFO = {'name': 'video-transcripts-detail', 'params': ['course_id']}

    def setUp(self):
        super(TestTranscriptsDetail, self).setUp()
        self.video = self._create_video_with_subs()

    def reverse_url(self, reverse_args=None, **kwargs):
        reverse_args = reverse_args or {}
        reverse_args.update({
            'block_id': self.video.location.block_id,
            'lang': kwargs.get('lang', 'en'),
        })
        return super(TestTranscriptsDetail, self).reverse_url(reverse_args, **kwargs)

    def test_incorrect_language(self):
        self.login_and_enroll()
        self.api_response(expected_response_code=404, lang='pl')

    def test_transcript_with_unicode_file_name(self):
        self.video = self._create_video_with_subs(custom_subid=u'你好')
        self.login_and_enroll()
        self.api_response(expected_response_code=200, lang='en')
