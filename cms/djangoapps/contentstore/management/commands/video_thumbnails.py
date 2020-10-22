"""
Command to scrape thumbnails and add them to the course-videos.
"""
import logging
from six import text_type

import edxval.api as edxval_api
from django.core.management import BaseCommand
from django.core.management.base import CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.video_config.models import VideoThumbnailSetting
from cms.djangoapps.contentstore.tasks import enqueue_update_thumbnail_tasks

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py cms video_thumbnails
    """
    help = 'Adds thumbnails from YouTube to videos'

    def _get_command_options(self):
        """
        Returns the command arguments configured via django admin.
        """
        command_settings = self._latest_settings()
        commit = command_settings.commit
        if command_settings.all_course_videos:
            course_videos = edxval_api.get_course_video_ids_with_youtube_profile(
                offset=command_settings.offset, limit=command_settings.batch_size
            )
            log.info(
                '[Video Thumbnails] Videos(updated): %s, Videos(update-in-process): %s',
                command_settings.offset, len(course_videos),
            )
        else:
            validated_course_ids = self._validate_course_ids(command_settings.course_ids.split())
            course_videos = edxval_api.get_course_video_ids_with_youtube_profile(validated_course_ids)

        return course_videos, commit

    def _validate_course_ids(self, course_ids):
        """
        Validate a list of course key strings.
        """
        try:
            for course_id in course_ids:
                CourseKey.from_string(course_id)
            return course_ids
        except InvalidKeyError as error:
            raise CommandError('Invalid key specified: {}'.format(text_type(error)))

    def _latest_settings(self):
        """
        Return the latest version of the VideoThumbnailSetting
        """
        return VideoThumbnailSetting.current()

    def handle(self, *args, **options):
        """
        Invokes the video thumbnail enqueue function.
        """
        video_thumbnail_settings = self._latest_settings()
        videos_per_task = video_thumbnail_settings.videos_per_task

        course_videos, commit = self._get_command_options()

        if commit:
            command_run = video_thumbnail_settings.increment_run()
            enqueue_update_thumbnail_tasks(
                course_videos=course_videos,
                videos_per_task=videos_per_task,
                run=command_run
            )
            if video_thumbnail_settings.all_course_videos:
                video_thumbnail_settings.update_offset()
        else:
            log.info('[video thumbnails] selected course videos: {course_videos} '.format(
                course_videos=text_type(course_videos)
            ))
