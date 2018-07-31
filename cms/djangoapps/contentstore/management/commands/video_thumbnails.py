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

from openedx.core.djangoapps.video_config.models import VideoThumbnailSetting, UpdatedCourseVideos
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
            all_course_videos = edxval_api.get_course_video_ids_with_youtube_profile()
            updated_course_videos = UpdatedCourseVideos.objects.all().values_list('course_id', 'edx_video_id')
            non_updated_course_videos = [
                course_video
                for course_video in all_course_videos
                if (course_video[0], course_video[1]) not in list(updated_course_videos)
            ]
            # Course videos for whom video thumbnails need to be updated
            course_videos = non_updated_course_videos[:command_settings.batch_size]

            log.info(
                ('[Video Thumbnails] Videos(total): %s, '
                 'Videos(updated): %s, Videos(non-updated): %s, '
                 'Videos(update-in-process): %s'),
                len(all_course_videos),
                len(updated_course_videos),
                len(non_updated_course_videos),
                len(course_videos),
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
                for course_id, edx_video_id, __ in course_videos:
                    UpdatedCourseVideos.objects.get_or_create(
                        course_id=course_id,
                        edx_video_id=edx_video_id,
                        command_run=command_run
                    )
        else:
            log.info('[video thumbnails] selected course videos: {course_videos} '.format(
                course_videos=text_type(course_videos)
            ))
