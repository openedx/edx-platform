# -*- coding: utf-8 -*-
"""
Tests for course transcript migration management command.
"""
import itertools
import logging
from datetime import datetime
import pytz

import ddt
from django.test import TestCase
from django.core.management import call_command, CommandError
from mock import patch

from openedx.core.djangoapps.video_config.models import (
    TranscriptMigrationSetting, MigrationEnqueuedCourse
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.video_module.transcripts_utils import save_to_store
from edxval import api as api
from testfixtures import LogCapture

LOGGER_NAME = "cms.djangoapps.contentstore.tasks"

SRT_FILEDATA = '''
0
00:00:00,270 --> 00:00:02,720
sprechen sie deutsch?

1
00:00:02,720 --> 00:00:05,430
Ja, ich spreche Deutsch

2
00:00:6,500 --> 00:00:08,600
可以用“我不太懂艺术 但我知道我喜欢什么”做比喻
'''

CRO_SRT_FILEDATA = '''
0
00:00:00,270 --> 00:00:02,720
Dobar dan!

1
00:00:02,720 --> 00:00:05,430
Kako ste danas?

2
00:00:6,500 --> 00:00:08,600
可以用“我不太懂艺术 但我知道我喜欢什么”做比喻
'''


VIDEO_DICT_STAR = dict(
    client_video_id='TWINKLE TWINKLE',
    duration=42.0,
    edx_video_id='test_edx_video_id',
    status='upload',
)


class TestArgParsing(TestCase):
    """
    Tests for parsing arguments for the `migrate_transcripts` management command
    """
    def test_no_args(self):
        errstring = "Must specify exactly one of --course_ids, --all_courses, --from_settings"
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('migrate_transcripts')

    def test_invalid_course(self):
        errstring = "Invalid course_key: 'invalid-course'."
        with self.assertRaisesRegexp(CommandError, errstring):
            call_command('migrate_transcripts', '--course-id', 'invalid-course')


@ddt.ddt
class TestMigrateTranscripts(ModuleStoreTestCase):
    """
    Tests migrating video transcripts in courses from contentstore to django storage
    """
    def setUp(self):
        """ Common setup. """
        super(TestMigrateTranscripts, self).setUp()
        self.store = modulestore()
        self.course = CourseFactory.create()
        self.course_2 = CourseFactory.create()

        video = {
            'edx_video_id': 'test_edx_video_id',
            'client_video_id': 'test1.mp4',
            'duration': 42.0,
            'status': 'upload',
            'courses': [unicode(self.course.id)],
            'encoded_videos': [],
            'created': datetime.now(pytz.utc)
        }
        api.create_video(video)

        video_sample_xml = '''
            <video display_name="Test Video"
                   edx_video_id="test_edx_video_id"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   download_track="false"
                   start_time="00:00:01"
                   download_video="false"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
              <handout src="http://www.example.com/handout"/>
              <transcript language="ge" src="subs_grmtran1.srt" />
              <transcript language="hr" src="subs_croatian1.srt" />
            </video>
        '''

        video_sample_xml_2 = '''
            <video display_name="Test Video 2"
                   edx_video_id="test_edx_video_id_2"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   download_track="false"
                   start_time="00:00:01"
                   download_video="false"
                   end_time="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
              <handout src="http://www.example.com/handout"/>
              <transcript language="ge" src="not_found.srt" />
            </video>
        '''
        self.video_descriptor = ItemFactory.create(
            parent_location=self.course.location, category='video',
            data={'data': video_sample_xml}
        )
        self.video_descriptor_2 = ItemFactory.create(
            parent_location=self.course_2.location, category='video',
            data={'data': video_sample_xml_2}
        )

        save_to_store(SRT_FILEDATA, 'subs_grmtran1.srt', 'text/srt', self.video_descriptor.location)
        save_to_store(CRO_SRT_FILEDATA, 'subs_croatian1.srt', 'text/srt', self.video_descriptor.location)

    def test_migrated_transcripts_count_with_commit(self):
        """
        Test migrating transcripts with commit
        """
        # check that transcript does not exist
        languages = api.get_available_transcript_languages(self.video_descriptor.edx_video_id)
        self.assertEqual(len(languages), 0)
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

        # now call migrate_transcripts command and check the transcript availability
        call_command('migrate_transcripts', '--course-id', unicode(self.course.id), '--commit')

        languages = api.get_available_transcript_languages(self.video_descriptor.edx_video_id)
        self.assertEqual(len(languages), 2)
        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

    def test_migrated_transcripts_without_commit(self):
        """
        Test migrating transcripts as a dry-run
        """
        # check that transcripts do not exist
        languages = api.get_available_transcript_languages(self.video_descriptor.edx_video_id)
        self.assertEqual(len(languages), 0)
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

        # now call migrate_transcripts command and check the transcript availability
        call_command('migrate_transcripts', '--course-id', unicode(self.course.id))

        # check that transcripts still do not exist
        languages = api.get_available_transcript_languages(self.video_descriptor.edx_video_id)
        self.assertEqual(len(languages), 0)
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

    def test_migrate_transcripts_availability(self):
        """
        Test migrating transcripts
        """
        translations = self.video_descriptor.available_translations(self.video_descriptor.get_transcripts_info())
        self.assertItemsEqual(translations, ['hr', 'ge'])
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

        # now call migrate_transcripts command and check the transcript availability
        call_command('migrate_transcripts', '--course-id', unicode(self.course.id), '--commit')

        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

    def test_migrate_transcripts_idempotency(self):
        """
        Test migrating transcripts multiple times
        """
        translations = self.video_descriptor.available_translations(self.video_descriptor.get_transcripts_info())
        self.assertItemsEqual(translations, ['hr', 'ge'])
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertFalse(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

        # now call migrate_transcripts command and check the transcript availability
        call_command('migrate_transcripts', '--course-id', unicode(self.course.id), '--commit')

        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

        # now call migrate_transcripts command again and check the transcript availability
        call_command('migrate_transcripts', '--course-id', unicode(self.course.id), '--commit')

        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

        # now call migrate_transcripts command with --force-update and check the transcript availability
        call_command('migrate_transcripts', '--course-id', unicode(self.course.id), '--force-update', '--commit')

        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'hr'))
        self.assertTrue(api.is_transcript_available(self.video_descriptor.edx_video_id, 'ge'))

    def test_migrate_transcripts_logging(self):
        """
        Test migrate transcripts logging and output
        """
        course_id = unicode(self.course.id)
        expected_log = (
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=-1] [video-transcripts-migration-process-started-for-course] '
                 u'[course={}]'.format(course_id))
            ),
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=-1] [video-transcript-will-be-migrated] '
                 u'[revision=rev-opt-published-only] [video={}] [edx_video_id=test_edx_video_id] '
                 u'[language_code=hr]'.format(self.video_descriptor.location))
            ),
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=-1] [video-transcript-will-be-migrated] '
                 u'[revision=rev-opt-published-only] [video={}] [edx_video_id=test_edx_video_id] '
                 u'[language_code=ge]'.format(self.video_descriptor.location))
            ),
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=-1] [transcripts-migration-tasks-submitted] '
                 u'[transcripts_count=2] [course={}] '
                 u'[revision=rev-opt-published-only] [video={}]'.format(course_id, self.video_descriptor.location))
            )
        )

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('migrate_transcripts', '--course-id', unicode(self.course.id))
            logger.check(
                *expected_log
            )

    def test_migrate_transcripts_exception_logging(self):
        """
        Test migrate transcripts exception logging
        """
        course_id = unicode(self.course_2.id)
        expected_log = (
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=1] [video-transcripts-migration-process-started-for-course] '
                 u'[course={}]'.format(course_id))
            ),
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=1] [transcripts-migration-process-started-for-video-transcript] '
                 u'[revision=rev-opt-published-only] [video={}] [edx_video_id=test_edx_video_id_2] '
                 u'[language_code=ge]'.format(self.video_descriptor_2.location))
            ),
            (
                'cms.djangoapps.contentstore.tasks', 'ERROR',
                (u'[Transcript Migration] [run=1] [video-transcript-migration-failed-with-known-exc] '
                 u'[revision=rev-opt-published-only] [video={}] [edx_video_id=test_edx_video_id_2] '
                 u'[language_code=ge]'.format(self.video_descriptor_2.location))
            ),
            (
                'cms.djangoapps.contentstore.tasks', 'INFO',
                (u'[Transcript Migration] [run=1] [transcripts-migration-tasks-submitted] '
                 u'[transcripts_count=1] [course={}] '
                 u'[revision=rev-opt-published-only] [video={}]'.format(course_id, self.video_descriptor_2.location))
            )
        )

        with LogCapture(LOGGER_NAME, level=logging.INFO) as logger:
            call_command('migrate_transcripts', '--course-id', unicode(self.course_2.id), '--commit')
            logger.check(
                *expected_log
            )

    @ddt.data(*itertools.product([1, 2], [True, False], [True, False]))
    @ddt.unpack
    @patch('contentstore.management.commands.migrate_transcripts.log')
    def test_migrate_transcripts_batch_size(self, batch_size, commit, all_courses, mock_logger):
        """
        Test that migrations across course batches, is working as expected.
        """
        migration_settings = TranscriptMigrationSetting.objects.create(
            batch_size=batch_size, commit=commit, all_courses=all_courses
        )

        # Assert the number of job runs and migration enqueued courses.
        self.assertEqual(migration_settings.command_run, 0)
        self.assertEqual(MigrationEnqueuedCourse.objects.count(), 0)

        call_command('migrate_transcripts', '--from-settings')

        migration_settings = TranscriptMigrationSetting.current()
        # Command run is only incremented if commit=True.
        expected_command_run = 1 if commit else 0
        self.assertEqual(migration_settings.command_run, expected_command_run)

        if all_courses:
            mock_logger.info.assert_called_with(
                ('[Transcript Migration] Courses(total): %s, Courses(migrated): %s, '
                 'Courses(non-migrated): %s, Courses(migration-in-process): %s'),
                2, 0, 2, batch_size
            )

        # enqueued courses are only persisted if commit=True and job is running for all courses.
        enqueued_courses = batch_size if commit and all_courses else 0
        self.assertEqual(MigrationEnqueuedCourse.objects.count(), enqueued_courses)
