# -*- coding: utf-8 -*-
"""
Tests for course video thumbnails management command.
"""
import logging
from mock import patch
from django.core.management import call_command, CommandError
from django.test import TestCase
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.video_config.models import VideoThumbnailSetting
from six import text_type
from testfixtures import LogCapture

LOGGER_NAME = "contentstore.management.commands.video_thumbnails"


def setup_video_thumbnails_config(batch_size=10, commit=False, all_course_videos=False, course_ids=''):
    VideoThumbnailSetting.objects.create(
        batch_size=batch_size,
        commit=commit,
        course_ids=course_ids,
        all_course_videos=all_course_videos,
        videos_per_task=2
    )


class TestArgParsing(TestCase):
    """
    Tests for parsing arguments for the `video_thumbnails` management command
    """
    def test_invalid_course(self):
        errstring = "Invalid key specified: <class 'opaque_keys.edx.locator.CourseLocator'>: invalid-course"
        setup_video_thumbnails_config(course_ids='invalid-course')
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('video_thumbnails')


class TestVideoThumbnails(ModuleStoreTestCase):
    """
    Tests adding thumbnails to course videos from YouTube
    """
    def setUp(self):
        """ Common setup """
        super(TestVideoThumbnails, self).setUp()
        self.course = CourseFactory.create()
        self.course_2 = CourseFactory.create()

    @patch('edxval.api.get_course_video_ids_with_youtube_profile')
    @patch('contentstore.management.commands.video_thumbnails.enqueue_update_thumbnail_tasks')
    def test_video_thumbnails_without_commit(self, mock_enqueue_thumbnails, mock_course_videos):
        """
        Test that when command is run without commit, correct information is logged.
        """
        course_videos = [
            (self.course.id, 'super-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP80'),
            (self.course_2.id, 'medium-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP81')
        ]
        mock_course_videos.return_value = course_videos

        setup_video_thumbnails_config(all_course_videos=True)

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('video_thumbnails')
            # Verify that list of course video ids is logged.
            logger.check(
                (
                    LOGGER_NAME, 'INFO',
                    '[Video Thumbnails] Videos(updated): 0, Videos(update-in-process): 2'
                ),
                (
                    LOGGER_NAME, 'INFO',
                    '[video thumbnails] selected course videos: {course_videos} '.format(
                        course_videos=text_type(course_videos)
                    )
                )
            )

            # Verify that `enqueue_update_thumbnail_tasks` is not called.
            self.assertFalse(mock_enqueue_thumbnails.called)

    @patch('edxval.api.get_course_video_ids_with_youtube_profile')
    @patch('contentstore.management.commands.video_thumbnails.enqueue_update_thumbnail_tasks')
    def test_video_thumbnails_with_commit(self, mock_enqueue_thumbnails, mock_course_videos):
        """
        Test that when command is run with with commit, it works as expected.
        """
        course_videos = [
            (self.course.id, 'super-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP80'),
            (self.course_2.id, 'medium-soaker', 'https://www.youtube.com/watch?v=OscRe3pSP81')
        ]
        mock_course_videos.return_value = course_videos
        setup_video_thumbnails_config(commit=True, all_course_videos=True)
        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('video_thumbnails')
            # Verify that command information correctly logged.
            logger.check((
                LOGGER_NAME, 'INFO',
                '[Video Thumbnails] Videos(updated): 0, Videos(update-in-process): 2'
            ))
            # Verify that `enqueue_update_thumbnail_tasks` is called.
            self.assertTrue(mock_enqueue_thumbnails.called)

    @patch('edxval.api.get_course_video_ids_with_youtube_profile')
    @patch('contentstore.video_utils.download_youtube_video_thumbnail')  # Mock(side_effect=Exception())
    def test_video_thumbnails_scraping_failed(self, mock_scrape_thumbnails, mock_course_videos):
        """
        Test that when scraping fails, it is handled correclty.
        """
        course_videos = [
            (self.course.id, 'super-soaker', 'OscRe3pSP80'),
            (self.course_2.id, 'medium-soaker', 'OscRe3pSP81')
        ]
        mock_scrape_thumbnails.side_effect = Exception('error')
        mock_course_videos.return_value = course_videos
        setup_video_thumbnails_config(commit=True, all_course_videos=True)

        tasks_logger = "cms.djangoapps.contentstore.tasks"
        with LogCapture(tasks_logger, level=logging.INFO) as logger:
            call_command('video_thumbnails')
            # Verify that tasks information is correctly logged.
            logger.check(
                (
                    tasks_logger, 'ERROR',
                    ("[video thumbnails] [run=1] [video-thumbnails-scraping-failed-with-unknown-exc] "
                     "[edx_video_id=super-soaker] [youtube_id=OscRe3pSP80] [course={}]".format(self.course.id))
                ),
                (
                    tasks_logger, 'ERROR',
                    ("[video thumbnails] [run=1] [video-thumbnails-scraping-failed-with-unknown-exc] "
                     "[edx_video_id=medium-soaker] [youtube_id=OscRe3pSP81] [course={}]".format(self.course_2.id))
                )
            )
