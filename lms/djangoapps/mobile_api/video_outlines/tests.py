"""
Tests for video outline API
"""
# pylint: disable=no-member
from uuid import uuid4
from collections import namedtuple

from edxval import api
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.video_module import transcripts_utils
from xmodule.modulestore.django import modulestore

from ..testutils import MobileAPITestCase, MobileAuthTestMixin, MobileEnrolledCourseAccessTestMixin


class TestVideoAPITestCase(MobileAPITestCase):
    """
    Base test class for video related mobile APIs
    """
    def setUp(self):
        super(TestVideoAPITestCase, self).setUp()
        self.section = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name=u"test factory section omega \u03a9",
        )
        self.sub_section = ItemFactory.create(
            parent_location=self.section.location,
            category="sequential",
            display_name=u"test subsection omega \u03a9",
        )

        self.unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit omega \u03a9",
        )
        self.other_unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=u"test unit omega 2 \u03a9",
        )
        self.nameless_unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'},
            display_name=None,
        )
        self.split_unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            display_name=u"split test vertical\u03a9",
        )

        self.split_test = ItemFactory.create(
            parent_location=self.split_unit.location,
            category="split_test",
            display_name=u"split test unit"
        )

        self.edx_video_id = 'testing-123'

        self.video_url = 'http://val.edx.org/val/video.mp4'
        self.html5_video_url = 'http://video.edx.org/html5/video.mp4'

        api.create_profile({
            'profile_name': 'youtube',
            'extension': 'mp4',
            'width': 1280,
            'height': 720
        })
        api.create_profile({
            'profile_name': 'mobile_low',
            'extension': 'mp4',
            'width': 640,
            'height': 480
        })

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
                }
            ]})

    def _create_video_with_subs(self):
        """
        Creates and returns a video with stored subtitles.
        """
        subid = uuid4().hex
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
            parent_location=self.unit.location,
            category="video",
            edx_video_id=self.edx_video_id,
            display_name=u"test video omega \u03a9",
            sub=subid
        )


class TestNonStandardCourseStructure(MobileAPITestCase):
    """
    Tests /api/mobile/v0.5/video_outlines/courses/{course_id} with no course set
    """
    REVERSE_INFO = {'name': 'video-summary-list', 'params': ['course_id']}

    def _verify_paths(self, course_outline, path_list):
        """
        Takes a path_list and compares it against the course_outline

        Attributes:
            path_list (list): A list of the expected strings
            course_outline (list): A list of dictionaries that includes a 'path'
                and 'named_path' field which we will be comparing path_list to
        """
        path = course_outline[0]['path']
        self.assertEqual(len(path), len(path_list))
        for i in range(0, len(path_list)):
            self.assertEqual(path_list[i], path[i]['name'])
        #named_path will be deprecated eventually
        named_path = course_outline[0]['named_path']
        self.assertEqual(len(named_path), len(path_list))
        for i in range(0, len(path_list)):
            self.assertEqual(path_list[i], named_path[i])

    def setUp(self):
        super(TestNonStandardCourseStructure, self).setUp()
        self.chapter_under_course = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name=u"test factory chapter under course omega \u03a9",
        )
        self.section_under_course = ItemFactory.create(
            parent_location=self.course.location,
            category="sequential",
            display_name=u"test factory section under course omega \u03a9",
        )
        self.section_under_chapter = ItemFactory.create(
            parent_location=self.chapter_under_course.location,
            category="sequential",
            display_name=u"test factory section under chapter omega \u03a9",
        )
        self.vertical_under_course = ItemFactory.create(
            parent_location=self.course.location,
            category="vertical",
            display_name=u"test factory vertical under course omega \u03a9",
        )
        self.vertical_under_section = ItemFactory.create(
            parent_location=self.section_under_chapter.location,
            category="vertical",
            display_name=u"test factory vertical under section omega \u03a9",
        )

    def test_structure_course_video(self):
        """
        Tests when there is a video without a vertical directly under course
        """
        self.login_and_enroll()
        ItemFactory.create(
            parent_location=self.course.location,
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
            parent_location=self.vertical_under_course.location,
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
            parent_location=self.chapter_under_course.location,
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
            parent_location=self.section_under_course.location,
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
            parent_location=self.section_under_chapter.location,
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
            parent_location=self.vertical_under_section.location,
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


class TestVideoSummaryList(TestVideoAPITestCase, MobileAuthTestMixin, MobileEnrolledCourseAccessTestMixin):
    """
    Tests for /api/mobile/v0.5/video_outlines/courses/{course_id}..
    """
    REVERSE_INFO = {'name': 'video-summary-list', 'params': ['course_id']}

    def test_course_list(self):
        self.login_and_enroll()
        self._create_video_with_subs()
        ItemFactory.create(
            parent_location=self.other_unit.location,
            category="video",
            display_name=u"test video omega 2 \u03a9",
            html5_sources=[self.html5_video_url]
        )
        ItemFactory.create(
            parent_location=self.other_unit.location,
            category="video",
            display_name=u"test video omega 3 \u03a9",
            source=self.html5_video_url
        )
        ItemFactory.create(
            parent_location=self.unit.location,
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
        self.assertEqual(course_outline[1]['summary']['video_url'], self.html5_video_url)
        self.assertEqual(course_outline[1]['summary']['size'], 0)
        self.assertEqual(course_outline[1]['path'][2]['name'], self.other_unit.display_name)
        self.assertEqual(course_outline[1]['path'][2]['id'], unicode(self.other_unit.location))

        self.assertEqual(course_outline[2]['summary']['video_url'], self.html5_video_url)
        self.assertEqual(course_outline[2]['summary']['size'], 0)

    def test_with_nameless_unit(self):
        self.login_and_enroll()
        ItemFactory.create(
            parent_location=self.nameless_unit.location,
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
            parent_location=self.sub_section.location,
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

    def test_with_split_test(self):
        self.login_and_enroll()

        ItemFactory.create(
            parent_location=self.split_test.location,
            category="video",
            display_name=u"split test video a",
        )
        ItemFactory.create(
            parent_location=self.split_test.location,
            category="video",
            display_name=u"split test video b",
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 2)
        self.assertEqual(len(course_outline[0]["path"]), 4)
        self.assertEqual(len(course_outline[1]["path"]), 4)
        self.assertEqual(course_outline[0]["summary"]["name"], u"split test video a")
        self.assertEqual(course_outline[1]["summary"]["name"], u"split test video b")

    def test_with_hidden_blocks(self):
        self.login_and_enroll()
        hidden_subsection = ItemFactory.create(
            parent_location=self.section.location,
            category="sequential",
            hide_from_toc=True,
        )
        unit_within_hidden_subsection = ItemFactory.create(
            parent_location=hidden_subsection.location,
            category="vertical",
        )
        hidden_unit = ItemFactory.create(
            parent_location=self.sub_section.location,
            category="vertical",
            hide_from_toc=True,
        )
        ItemFactory.create(
            parent_location=unit_within_hidden_subsection.location,
            category="video",
            edx_video_id=self.edx_video_id,
        )
        ItemFactory.create(
            parent_location=hidden_unit.location,
            category="video",
            edx_video_id=self.edx_video_id,
        )
        course_outline = self.api_response().data
        self.assertEqual(len(course_outline), 0)

    def test_language(self):
        self.login_and_enroll()
        video = ItemFactory.create(
            parent_location=self.nameless_unit.location,
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
            parent_location=self.nameless_unit.location,
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


class TestTranscriptsDetail(TestVideoAPITestCase, MobileAuthTestMixin, MobileEnrolledCourseAccessTestMixin):
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
