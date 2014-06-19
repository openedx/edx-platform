import copy
import json
import tempfile

from boto.exception import S3ResponseError
from datetime import datetime, timedelta
from mock import patch, ANY
from pymongo import MongoClient
from uuid import uuid4

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test.utils import override_settings

from contentstore.tests.modulestore_config import TEST_MODULESTORE
from contentstore.management.commands.update_transcripts import Command
TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.exceptions import NotFoundError
from xmodule.modulestore import Location
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore, loc_mapper, clear_existing_modulestores
from xmodule.modulestore.locator import CourseLocator
from xmodule.video_module import transcripts_utils
from xmodule.video_module.transcripts_utils import GetTranscriptsFromYouTubeException


TRANSCRIPTS_BACKUP_BUCKET_NAME = 'dummy_bucket'
TRANSCRIPTS_BACKUP_DIR = 'dummy_dir'
AWS_ACCESS_KEY_ID = 'DUMMY_KEY_ID'
AWS_SECRET_ACCESS_KEY = 'DUMMY_ACCESS_KEY'

command_output_file = tempfile.NamedTemporaryFile()


@override_settings(TRANSCRIPTS_COMMAND_OUTPUT=command_output_file.name)
class TestArgParsing(ModuleStoreTestCase):
    """
    Tests for parsing arguments of the `update_transcripts` command
    """
    def setUp(self):
        self.command = Command()

    def test_too_much_args(self):
        """
        Tests for the case when too much args are specified
        """
        errstring = "update_transcripts requires one or no arguments"
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle('arg1', 'arg2')

    def test_invalid_course_id(self):
        """
        Tests for the case when invalid course_id is specified
        """
        errstring = "The course_id is not of the right format."
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle('this_is_not_the_right_format')

    @patch('contentstore.management.commands.update_transcripts.TranscriptS3Store')
    def test_not_found_course_id(self, mock_store_class):
        """
        Tests for the case when non-existing course_id is specified
        """
        errstring = "The specified course does not exist."
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle('does/not/exist')

    @patch('contentstore.management.commands.update_transcripts.TranscriptS3Store')
    def test_when_store_failed_to_connect(self, mock_store_class):
        """
        Tests for the case when S3 connection error raises
        """
        mock_store_class.side_effect = Exception("Failed to connect to S3.")

        errstring = "Could not establish a connection to S3 for transcripts backup."
        with self.assertRaisesRegexp(CommandError, errstring):
            self.command.handle('org/course/name')

        mock_store_class.assert_called_once_with()


@override_settings(TRANSCRIPTS_COMMAND_OUTPUT=command_output_file.name,
                   TRANSCRIPTS_BACKUP_BUCKET_NAME=TRANSCRIPTS_BACKUP_BUCKET_NAME,
                   TRANSCRIPTS_BACKUP_DIR=TRANSCRIPTS_BACKUP_DIR,
                   AWS_ACCESS_KEY_ID=AWS_ACCESS_KEY_ID,
                   AWS_SECRET_ACCESS_KEY=AWS_SECRET_ACCESS_KEY)
@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class TestUpdateTranscripts(ModuleStoreTestCase):
    """
    Tests for the process of the `update_transcripts` command
    """

    def setUp(self):
        super(TestUpdateTranscripts, self).setUp()

        # Course with 1 video item, the transcripts of which don't exist on local store
        self.course = CourseFactory.create(
            org='edX', course='001', display_name='Robot Super Course')
        ItemFactory.create(
            parent_location=self.course.location, category='video',
            data={'data': '''
                  <video display_name="Test Video"
                          youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                          show_captions="false"
                          from="00:00:01"
                          to="00:01:00">
                      <source src="http://www.example.com/file.mp4"/>
                      <track src="http://www.example.com/track"/>
                  </video>'''}
        )

        # Course with 1 video item, the transcripts of which already uploaded to local store
        self.course2 = CourseFactory.create(
            org='edX', course='002', display_name='Transcripts Already Exist Course')
        ItemFactory.create(
            parent_location=self.course2.location, category='video',
            data={'data': '''
                  <video display_name="Test Video"
                          youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                          show_captions="false"
                          from="00:00:01"
                          to="00:01:00">
                      <source src="http://www.example.com/file.mp4"/>
                      <track src="http://www.example.com/track"/>
                  </video>'''}
        )
        self.subs = {
            'start': [100, 200, 240, 390, 1000],
            'end': [200, 240, 380, 1000, 1500],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        self.changed_subs = {
            'start': [100],
            'end': [200],
            'text': ['subs #1']
        }
        subs_id = 'p2Q6BrNhdh8'
        filename = 'subs_{0}.srt.sjson'.format(subs_id)
        self.content_location = StaticContent.compute_location(
            self.course2.location.org, self.course2.location.course, filename
        )
        transcripts_utils.save_subs_to_store(self.subs, subs_id, self.course2)

        # Ended course
        past_end = datetime.now() - timedelta(days=12)
        self.course3 = CourseFactory.create(
            org='edX', course='003', display_name='Already Ended Course', end=past_end)

        # patcher
        patcher_conn = patch('contentstore.management.commands.update_transcripts.S3Connection')
        self.mock_conn_class = patcher_conn.start()
        self.mock_conn_class.return_value.get_bucket.return_value = None
        self.addCleanup(patcher_conn.stop)

        patcher_get_transcripts = patch('xmodule.video_module.transcripts_utils.get_transcripts_from_youtube')
        self.mock_get_transcripts = patcher_get_transcripts.start()
        self.mock_get_transcripts.return_value = self.subs
        self.addCleanup(patcher_get_transcripts.stop)

        patcher_logger_info = patch('contentstore.management.commands.update_transcripts.log.info')
        self.logger_info = patcher_logger_info.start()
        self.addCleanup(patcher_logger_info.stop)

        self.addCleanup(ModuleStoreTestCase.drop_mongo_collections, 'split')
        self.addCleanup(clear_existing_modulestores)

    def tearDown(self):
        self.clear_subs_content()
        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'])
        _CONTENTSTORE.clear()

    def clear_subs_content(self):
        """Remove, if subtitles content exists."""
        try:
            content = contentstore().find(self.content_location)
            contentstore().delete(content.get_id())
        except NotFoundError:
            pass

    def test_course_with_no_transcripts_on_local_store(self):
        """
        Tests for the case when no transcripts exist on the local store
        """
        call_command('update_transcripts', self.course.location.course_id)

        self.mock_conn_class.assert_called_once_with(ANY, ANY)

        # assert info log
        self.assertIn("Success", self.logger_info.call_args[0][0])

    def test_course_raise_exception_when_get_transcripts_from_youtube(self):
        """
        Tests for the case when GetTranscriptsFromYouTubeException raises while getting transcripts from YouTube
        """
        self.mock_get_transcripts.side_effect = GetTranscriptsFromYouTubeException()

        call_command('update_transcripts', self.course.location.course_id)

        self.mock_conn_class.assert_called_once_with(ANY, ANY)
        self.assertEqual(2, self.mock_get_transcripts.call_count)

        # assert info log
        self.assertIn("Can't receive transcripts from YouTube", self.logger_info.call_args[0][0])

    @patch('contentstore.management.commands.update_transcripts.get_data_from_local')
    def test_course_with_changed_transcript(self, mock_get_data):
        """
        Tests for the case when the local transcript has some change from YouTube
        """
        mock_get_data.return_value = json.dumps(self.changed_subs)

        call_command('update_transcripts', self.course2.location.course_id)

        self.mock_conn_class.assert_called_once_with(ANY, ANY)
        self.mock_get_transcripts.assert_called_once_with(ANY, ANY, ANY)
        mock_get_data.assert_called_once_with(ANY, ANY)

        # assert info log
        self.assertIn("Success", self.logger_info.call_args[0][0])

    @patch('contentstore.management.commands.update_transcripts.get_data_from_local')
    def test_course_with_same_transcript(self, mock_get_data):
        """
        Tests for the case when the local transcript has no change from YouTube
        """
        mock_get_data.return_value = json.dumps(self.subs)

        call_command('update_transcripts', self.course2.location.course_id)

        self.mock_conn_class.assert_called_once_with(ANY, ANY)
        self.mock_get_transcripts.assert_called_once_with(ANY, ANY, ANY)
        mock_get_data.assert_called_once_with(ANY, ANY)

        # assert info log
        self.assertIn("No changes on YouTube", self.logger_info.call_args[0][0])

    @patch('contentstore.management.commands.update_transcripts.get_data_from_local')
    def test_course_raise_s3_response_error_when_store_failed_to_save(self, mock_get_data):
        """
        Tests for the case when S3ResponseError raises while saving the backup file to S3
        """
        mock_get_data.return_value = json.dumps(self.changed_subs)
        self.mock_conn_class.return_value.get_bucket.side_effect = S3ResponseError(404, "Not found.")

        call_command('update_transcripts', self.course2.location.course_id)

        self.mock_conn_class.assert_called_once_with(ANY, ANY)
        self.mock_get_transcripts.assert_called_once_with(ANY, ANY, ANY)
        mock_get_data.assert_called_once_with(ANY, ANY)
        self.mock_conn_class.return_value.get_bucket.assert_called_once_with(ANY)

        # assert info log
        self.assertIn("WARN: Failed to store backup file to S3", self.logger_info.call_args[0][0])

    def test_ended_course(self):
        """
        Tests for the case when processing the ended course
        """
        call_command('update_transcripts', self.course3.location.course_id)

        self.mock_conn_class.assert_called_once_with(ANY, ANY)

        # assert info log
        self.assertIn("This course has already ende", self.logger_info.call_args[0][0])

    def test_all_courses(self):
        """
        Tests for multiple courses
        """
        call_command('update_transcripts')

    @override_settings(TRANSCRIPTS_COMMAND_OUTPUT=None)
    def test_raise_unexpected_exception(self):
        """
        Tests for the case when unexpected exception raises while processing the command
        """
        with self.assertRaises(TypeError):
            call_command('update_transcripts')
