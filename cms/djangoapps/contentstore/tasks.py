"""
This file contains celery tasks for contentstore views
"""
from __future__ import absolute_import

import base64
import json
import os
import shutil
import tarfile
from datetime import datetime
from math import ceil
from tempfile import NamedTemporaryFile, mkdtemp

from celery import group
from celery.task import task
from celery.utils.log import get_task_logger
from celery_utils.chordable_django_backend import chord, chord_task
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.core.files.base import ContentFile
from django.test import RequestFactory
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext as _
from djcelery.common import respect_language
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator, BlockUsageLocator
from organizations.models import OrganizationCourse
from path import Path as path
from pytz import UTC
from six import iteritems, text_type
from user_tasks.models import UserTaskArtifact, UserTaskStatus
from user_tasks.tasks import UserTask

import dogstats_wrapper as dog_stats_api
from contentstore.courseware_index import CoursewareSearchIndexer, LibrarySearchIndexer, SearchIndexingError
from contentstore.storage import course_import_export_storage
from contentstore.utils import initialize_permissions, reverse_usage_url
from contentstore.video_utils import scrape_youtube_thumbnail
from course_action_state.models import CourseRerunState
from models.settings.course_metadata import CourseMetadata
from openedx.core.djangoapps.embargo.models import CountryAccessRule, RestrictedCourse
from openedx.core.lib.extract_tar import safetar_extractall
from student.auth import has_course_author_access
from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseFields
from xmodule.exceptions import SerializationError
from xmodule.modulestore import COURSE_ROOT, LIBRARY_ROOT
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError
from xmodule.modulestore.xml_exporter import export_course_to_xml, export_library_to_xml
from xmodule.modulestore.xml_importer import import_course_from_xml, import_library_from_xml
from xmodule.video_module.transcripts_utils import (
    Transcript,
    clean_video_id,
    get_transcript_from_contentstore,
    TranscriptsGenerationException
)
from xmodule.modulestore import ModuleStoreEnum
from xmodule.exceptions import NotFoundError
from edxval.api import (
    ValCannotCreateError,
    create_video_transcript,
    is_video_available,
    is_transcript_available,
    create_or_update_video_transcript,
    create_external_video,
)

User = get_user_model()

LOGGER = get_task_logger(__name__)
FILE_READ_CHUNK = 1024  # bytes
FULL_COURSE_REINDEX_THRESHOLD = 1
DEFAULT_ALL_COURSES = False
DEFAULT_FORCE_UPDATE = False
DEFAULT_COMMIT = False
MIGRATION_LOGS_PREFIX = 'Transcript Migration'

RETRY_DELAY_SECONDS = 30
COURSE_LEVEL_TIMEOUT_SECONDS = 1200
VIDEO_LEVEL_TIMEOUT_SECONDS = 300


def enqueue_update_thumbnail_tasks(course_videos, videos_per_task, run):
    """
    Enqueue tasks to update video thumbnails from youtube.

    Arguments:
        course_videos: A list of tuples, each containing course ID, video ID and youtube ID.
        videos_per_task: Number of course videos that can be processed by a single celery task.
        run: This tracks the YT thumbnail scraping job runs.
    """
    tasks = []
    batch_size = len(course_videos)
    # Further slice the course-videos batch into chunks on the
    # basis of number of course-videos per task.
    start = 0
    end = videos_per_task
    chunks_count = int(ceil(batch_size / float(videos_per_task)))
    for __ in xrange(0, chunks_count):
        course_videos_chunk = course_videos[start:end]
        tasks.append(task_scrape_youtube_thumbnail.s(
            course_videos_chunk, run
        ))
        start = end
        end += videos_per_task

    # Kick off a chord of scraping tasks
    callback = task_scrape_youtube_thumbnail_callback.s(
        run=run,
        batch_size=batch_size,
        videos_per_task=videos_per_task,
    )
    chord(tasks)(callback)


@chord_task(bind=True, routing_key=settings.VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE)
def task_scrape_youtube_thumbnail_callback(self, results, run,  # pylint: disable=unused-argument
                                           batch_size, videos_per_task):
    """
    Callback for collating the results of yt thumbnails scraping tasks chord.
    """
    yt_thumbnails_scraping_tasks_count = len(list(results()))
    LOGGER.info(
        ("[video thumbnails] [run=%s] [video-thumbnails-scraping-complete-for-a-batch] [tasks_count=%s] "
         "[batch_size=%s] [videos_per_task=%s]"),
        run, yt_thumbnails_scraping_tasks_count, batch_size, videos_per_task
    )


@chord_task(
    bind=True,
    base=LoggedPersistOnFailureTask,
    default_retry_delay=RETRY_DELAY_SECONDS,
    max_retries=1,
    time_limit=COURSE_LEVEL_TIMEOUT_SECONDS,
    routing_key=settings.SCRAPE_YOUTUBE_THUMBNAILS_JOB_QUEUE
)
def task_scrape_youtube_thumbnail(self, course_videos, run):   # pylint: disable=unused-argument
    """
    Task to scrape youtube thumbnails and update them in edxval for the given course-videos.

    Arguments:
        course_videos: A list of tuples, each containing course ID, video ID and youtube ID.
        run: This tracks the YT thumbnail scraping job runs.
    """
    for course_id, edx_video_id, youtube_id in course_videos:
        try:
            scrape_youtube_thumbnail(course_id, edx_video_id, youtube_id)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception(
                ("[video thumbnails] [run=%s] [video-thumbnails-scraping-failed-with-unknown-exc] "
                 "[edx_video_id=%s] [youtube_id=%s] [course=%s]"),
                run,
                edx_video_id,
                youtube_id,
                course_id
            )
            continue


@chord_task(bind=True, routing_key=settings.VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE)
def task_status_callback(self, results, revision,  # pylint: disable=unused-argument
                         course_id, command_run, video_location):
    """
    Callback for collating the results of chord.
    """
    transcript_tasks_count = len(list(results()))

    LOGGER.info(
        ("[%s] [run=%s] [video-transcripts-migration-complete-for-a-video] [tasks_count=%s] [course_id=%s] "
         "[revision=%s] [video=%s]"),
        MIGRATION_LOGS_PREFIX, command_run, transcript_tasks_count, course_id, revision, video_location
    )


def enqueue_async_migrate_transcripts_tasks(course_keys,
                                            command_run,
                                            force_update=DEFAULT_FORCE_UPDATE,
                                            commit=DEFAULT_COMMIT):
    """
    Fires new Celery tasks for all the input courses or for all courses.

    Arguments:
        course_keys: Command line course ids as list of CourseKey objects
        command_run: A positive number indicating the run counts for transcripts migrations
        force_update: Overwrite file in S3. Default is False
        commit: Update S3 or dry-run the command to see which transcripts will be affected. Default is False
    """
    kwargs = {
        'force_update': force_update,
        'commit': commit,
        'command_run': command_run
    }
    group([
        async_migrate_transcript.s(unicode(course_key), **kwargs)
        for course_key in course_keys
    ])()


def get_course_videos(course_key):
    """
    Returns all videos in a course as list.

    Arguments:
        course_key: CourseKey object
    """
    all_videos = {}
    store = modulestore()

    # include published videos of the course.
    all_videos[ModuleStoreEnum.RevisionOption.published_only] = store.get_items(
        course_key,
        qualifiers={'category': 'video'},
        revision=ModuleStoreEnum.RevisionOption.published_only,
        include_orphans=False
    )

    # include draft videos of the course.
    all_videos[ModuleStoreEnum.RevisionOption.draft_only] = store.get_items(
        course_key,
        qualifiers={'category': 'video'},
        revision=ModuleStoreEnum.RevisionOption.draft_only,
        include_orphans=False
    )

    return all_videos


@chord_task(
    bind=True,
    base=LoggedPersistOnFailureTask,
    default_retry_delay=RETRY_DELAY_SECONDS,
    max_retries=1,
    time_limit=COURSE_LEVEL_TIMEOUT_SECONDS,
    routing_key=settings.VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE
)
def async_migrate_transcript(self, course_key, **kwargs):   # pylint: disable=unused-argument
    """
    Migrates the transcripts of all videos in a course as a new celery task.
    """
    force_update = kwargs['force_update']
    command_run = kwargs['command_run']
    course_videos = get_course_videos(CourseKey.from_string(course_key))

    LOGGER.info(
        "[%s] [run=%s] [video-transcripts-migration-process-started-for-course] [course=%s]",
        MIGRATION_LOGS_PREFIX, command_run, course_key
    )

    for revision, videos in course_videos.items():
        for video in videos:
            # Gather transcripts from a video block.
            all_transcripts = {}
            if video.transcripts is not None:
                all_transcripts.update(video.transcripts)

            english_transcript = video.sub
            if english_transcript:
                all_transcripts.update({'en': video.sub})

            sub_tasks = []
            video_location = unicode(video.location)
            for lang in all_transcripts:
                sub_tasks.append(async_migrate_transcript_subtask.s(
                    video_location, revision, lang, force_update, **kwargs
                ))

            if sub_tasks:
                callback = task_status_callback.s(
                    revision=revision,
                    course_id=course_key,
                    command_run=command_run,
                    video_location=video_location
                )
                chord(sub_tasks)(callback)

                LOGGER.info(
                    ("[%s] [run=%s] [transcripts-migration-tasks-submitted] "
                     "[transcripts_count=%s] [course=%s] [revision=%s] [video=%s]"),
                    MIGRATION_LOGS_PREFIX, command_run, len(sub_tasks), course_key, revision, video_location
                )
            else:
                LOGGER.info(
                    "[%s] [run=%s] [no-video-transcripts] [course=%s] [revision=%s] [video=%s]",
                    MIGRATION_LOGS_PREFIX, command_run, course_key, revision, video_location
                )


def save_transcript_to_storage(command_run, edx_video_id, language_code, transcript_content, file_format, force_update):
    """
    Pushes a given transcript's data to django storage.

    Arguments:
        command_run: A positive integer indicating the current run
        edx_video_id: video ID
        language_code: language code
        transcript_content: content of the transcript
        file_format: format of the transcript file
        force_update: tells whether it needs to perform force update in
        case of an existing transcript for the given video.
    """
    transcript_present = is_transcript_available(video_id=edx_video_id, language_code=language_code)
    if transcript_present and force_update:
        create_or_update_video_transcript(
            edx_video_id,
            language_code,
            dict({'file_format': file_format}),
            ContentFile(transcript_content)
        )
    elif not transcript_present:
        create_video_transcript(
            edx_video_id,
            language_code,
            file_format,
            ContentFile(transcript_content)
        )
    else:
        LOGGER.info(
            "[%s] [run=%s] [do-not-override-existing-transcript] [edx_video_id=%s] [language_code=%s]",
            MIGRATION_LOGS_PREFIX, command_run, edx_video_id, language_code
        )


@chord_task(
    bind=True,
    base=LoggedPersistOnFailureTask,
    default_retry_delay=RETRY_DELAY_SECONDS,
    max_retries=2,
    time_limit=VIDEO_LEVEL_TIMEOUT_SECONDS,
    routing_key=settings.VIDEO_TRANSCRIPT_MIGRATIONS_JOB_QUEUE
)
def async_migrate_transcript_subtask(self, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Migrates a transcript of a given video in a course as a new celery task.
    """
    success, failure = 'Success', 'Failure'
    video_location, revision, language_code, force_update = args
    command_run = kwargs['command_run']
    store = modulestore()
    video = store.get_item(usage_key=BlockUsageLocator.from_string(video_location), revision=revision)
    edx_video_id = clean_video_id(video.edx_video_id)

    if not kwargs['commit']:
        LOGGER.info(
            ('[%s] [run=%s] [video-transcript-will-be-migrated] '
             '[revision=%s] [video=%s] [edx_video_id=%s] [language_code=%s]'),
            MIGRATION_LOGS_PREFIX, command_run, revision, video_location, edx_video_id, language_code
        )
        return success

    LOGGER.info(
        ('[%s] [run=%s] [transcripts-migration-process-started-for-video-transcript] [revision=%s] '
         '[video=%s] [edx_video_id=%s] [language_code=%s]'),
        MIGRATION_LOGS_PREFIX, command_run, revision, video_location, edx_video_id, language_code
    )

    try:
        transcripts_info = video.get_transcripts_info()
        transcript_content, _, _ = get_transcript_from_contentstore(
            video=video,
            language=language_code,
            output_format=Transcript.SJSON,
            transcripts_info=transcripts_info,
        )

        is_video_valid = edx_video_id and is_video_available(edx_video_id)
        if not is_video_valid:
            edx_video_id = create_external_video('external-video')
            video.edx_video_id = edx_video_id

            # determine branch published/draft
            branch_setting = (
                ModuleStoreEnum.Branch.published_only
                if revision == ModuleStoreEnum.RevisionOption.published_only else
                ModuleStoreEnum.Branch.draft_preferred
            )
            with store.branch_setting(branch_setting):
                store.update_item(video, ModuleStoreEnum.UserID.mgmt_command)

            LOGGER.info(
                '[%s] [run=%s] [generated-edx-video-id] [revision=%s] [video=%s] [edx_video_id=%s] [language_code=%s]',
                MIGRATION_LOGS_PREFIX, command_run, revision, video_location, edx_video_id, language_code
            )

        save_transcript_to_storage(
            command_run=command_run,
            edx_video_id=edx_video_id,
            language_code=language_code,
            transcript_content=transcript_content,
            file_format=Transcript.SJSON,
            force_update=force_update,
        )
    except (NotFoundError, TranscriptsGenerationException, ValCannotCreateError):
        LOGGER.exception(
            ('[%s] [run=%s] [video-transcript-migration-failed-with-known-exc] [revision=%s] [video=%s] '
             '[edx_video_id=%s] [language_code=%s]'),
            MIGRATION_LOGS_PREFIX, command_run, revision, video_location, edx_video_id, language_code
        )
        return failure
    except Exception:
        LOGGER.exception(
            ('[%s] [run=%s] [video-transcript-migration-failed-with-unknown-exc] [revision=%s] '
             '[video=%s] [edx_video_id=%s] [language_code=%s]'),
            MIGRATION_LOGS_PREFIX, command_run, revision, video_location, edx_video_id, language_code
        )
        raise

    LOGGER.info(
        ('[%s] [run=%s] [video-transcript-migration-succeeded-for-a-video] [revision=%s] '
         '[video=%s] [edx_video_id=%s] [language_code=%s]'),
        MIGRATION_LOGS_PREFIX, command_run, revision, video_location, edx_video_id, language_code
    )
    return success


def clone_instance(instance, field_values):
    """ Clones a Django model instance.

    The specified fields are replaced with new values.

    Arguments:
        instance (Model): Instance of a Django model.
        field_values (dict): Map of field names to new values.

    Returns:
        Model: New instance.
    """
    instance.pk = None

    for field, value in iteritems(field_values):
        setattr(instance, field, value)

    instance.save()

    return instance


@task()
def rerun_course(source_course_key_string, destination_course_key_string, user_id, fields=None):
    """
    Reruns a course in a new celery task.
    """
    # import here, at top level this import prevents the celery workers from starting up correctly
    from edxval.api import copy_course_videos

    source_course_key = CourseKey.from_string(source_course_key_string)
    destination_course_key = CourseKey.from_string(destination_course_key_string)
    try:
        # deserialize the payload
        fields = deserialize_fields(fields) if fields else None

        # use the split modulestore as the store for the rerun course,
        # as the Mongo modulestore doesn't support multiple runs of the same course.
        store = modulestore()
        with store.default_store('split'):
            store.clone_course(source_course_key, destination_course_key, user_id, fields=fields)

        # set initial permissions for the user to access the course.
        initialize_permissions(destination_course_key, User.objects.get(id=user_id))

        # update state: Succeeded
        CourseRerunState.objects.succeeded(course_key=destination_course_key)

        # call edxval to attach videos to the rerun
        copy_course_videos(source_course_key, destination_course_key)

        # Copy OrganizationCourse
        organization_course = OrganizationCourse.objects.filter(course_id=source_course_key_string).first()

        if organization_course:
            clone_instance(organization_course, {'course_id': destination_course_key_string})

        # Copy RestrictedCourse
        restricted_course = RestrictedCourse.objects.filter(course_key=source_course_key).first()

        if restricted_course:
            country_access_rules = CountryAccessRule.objects.filter(restricted_course=restricted_course)
            new_restricted_course = clone_instance(restricted_course, {'course_key': destination_course_key})
            for country_access_rule in country_access_rules:
                clone_instance(country_access_rule, {'restricted_course': new_restricted_course})

        return "succeeded"

    except DuplicateCourseError:
        # do NOT delete the original course, only update the status
        CourseRerunState.objects.failed(course_key=destination_course_key)
        LOGGER.exception(u'Course Rerun Error')
        return "duplicate course"

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        CourseRerunState.objects.failed(course_key=destination_course_key)
        LOGGER.exception(u'Course Rerun Error')

        try:
            # cleanup any remnants of the course
            modulestore().delete_course(destination_course_key, user_id)
        except ItemNotFoundError:
            # it's possible there was an error even before the course module was created
            pass

        return u"exception: " + text_type(exc)


def deserialize_fields(json_fields):
    fields = json.loads(json_fields)
    for field_name, value in iteritems(fields):
        fields[field_name] = getattr(CourseFields, field_name).from_json(value)
    return fields


def _parse_time(time_isoformat):
    """ Parses time from iso format """
    return datetime.strptime(
        # remove the +00:00 from the end of the formats generated within the system
        time_isoformat.split('+')[0],
        "%Y-%m-%dT%H:%M:%S.%f"
    ).replace(tzinfo=UTC)


@task()
def update_search_index(course_id, triggered_time_isoformat):
    """ Updates course search index. """
    try:
        course_key = CourseKey.from_string(course_id)
        CoursewareSearchIndexer.index(modulestore(), course_key, triggered_at=(_parse_time(triggered_time_isoformat)))

    except SearchIndexingError as exc:
        LOGGER.error(u'Search indexing error for complete course %s - %s', course_id, text_type(exc))
    else:
        LOGGER.debug(u'Search indexing successful for complete course %s', course_id)


@task()
def update_library_index(library_id, triggered_time_isoformat):
    """ Updates course search index. """
    try:
        library_key = CourseKey.from_string(library_id)
        LibrarySearchIndexer.index(modulestore(), library_key, triggered_at=(_parse_time(triggered_time_isoformat)))

    except SearchIndexingError as exc:
        LOGGER.error(u'Search indexing error for library %s - %s', library_id, text_type(exc))
    else:
        LOGGER.debug(u'Search indexing successful for library %s', library_id)


@task()
def push_course_update_task(course_key_string, course_subscription_id, course_display_name):
    """
    Sends a push notification for a course update.
    """
    # TODO Use edx-notifications library instead (MA-638).
    from .push_notification import send_push_course_update
    send_push_course_update(course_key_string, course_subscription_id, course_display_name)


class CourseExportTask(UserTask):  # pylint: disable=abstract-method
    """
    Base class for course and library export tasks.
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get the number of in-progress steps in the export process, as shown in the UI.

        For reference, these are:

        1. Exporting
        2. Compressing
        """
        return 2

    @classmethod
    def generate_name(cls, arguments_dict):
        """
        Create a name for this particular import task instance.

        Arguments:
            arguments_dict (dict): The arguments given to the task function

        Returns:
            text_type: The generated name
        """
        key = arguments_dict[u'course_key_string']
        return u'Export of {}'.format(key)


@task(base=CourseExportTask, bind=True)
def export_olx(self, user_id, course_key_string, language):
    """
    Export a course or library to an OLX .tar.gz archive and prepare it for download.
    """
    courselike_key = CourseKey.from_string(course_key_string)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        with respect_language(language):
            self.status.fail(_(u'Unknown User ID: {0}').format(user_id))
        return
    if not has_course_author_access(user, courselike_key):
        with respect_language(language):
            self.status.fail(_(u'Permission denied'))
        return

    if isinstance(courselike_key, LibraryLocator):
        courselike_module = modulestore().get_library(courselike_key)
    else:
        courselike_module = modulestore().get_course(courselike_key)

    try:
        self.status.set_state(u'Exporting')
        tarball = create_export_tarball(courselike_module, courselike_key, {}, self.status)
        artifact = UserTaskArtifact(status=self.status, name=u'Output')
        artifact.file.save(name=os.path.basename(tarball.name), content=File(tarball))  # pylint: disable=no-member
        artifact.save()
    # catch all exceptions so we can record useful error messages
    except Exception as exception:  # pylint: disable=broad-except
        LOGGER.exception(u'Error exporting course %s', courselike_key, exc_info=True)
        if self.status.state != UserTaskStatus.FAILED:
            self.status.fail({'raw_error_msg': text_type(exception)})
        return


def create_export_tarball(course_module, course_key, context, status=None):
    """
    Generates the export tarball, or returns None if there was an error.

    Updates the context with any error information if applicable.
    """
    name = course_module.url_name
    export_file = NamedTemporaryFile(prefix=name + '.', suffix=".tar.gz")
    root_dir = path(mkdtemp())

    try:
        if isinstance(course_key, LibraryLocator):
            export_library_to_xml(modulestore(), contentstore(), course_key, root_dir, name)
        else:
            export_course_to_xml(modulestore(), contentstore(), course_module.id, root_dir, name)

        if status:
            status.set_state(u'Compressing')
            status.increment_completed_steps()
        LOGGER.debug(u'tar file being generated at %s', export_file.name)
        with tarfile.open(name=export_file.name, mode='w:gz') as tar_file:
            tar_file.add(root_dir / name, arcname=name)

    except SerializationError as exc:
        LOGGER.exception(u'There was an error exporting %s', course_key, exc_info=True)
        parent = None
        try:
            failed_item = modulestore().get_item(exc.location)
            parent_loc = modulestore().get_parent_location(failed_item.location)

            if parent_loc is not None:
                parent = modulestore().get_item(parent_loc)
        except:  # pylint: disable=bare-except
            # if we have a nested exception, then we'll show the more generic error message
            pass

        context.update({
            'in_err': True,
            'raw_err_msg': str(exc),
            'edit_unit_url': reverse_usage_url("container_handler", parent.location) if parent else "",
        })
        if status:
            status.fail(json.dumps({'raw_error_msg': context['raw_err_msg'],
                                    'edit_unit_url': context['edit_unit_url']}))
        raise
    except Exception as exc:
        LOGGER.exception('There was an error exporting %s', course_key, exc_info=True)
        context.update({
            'in_err': True,
            'edit_unit_url': None,
            'raw_err_msg': str(exc)})
        if status:
            status.fail(json.dumps({'raw_error_msg': context['raw_err_msg']}))
        raise
    finally:
        if os.path.exists(root_dir / name):
            shutil.rmtree(root_dir / name)

    return export_file


class CourseImportTask(UserTask):  # pylint: disable=abstract-method
    """
    Base class for course and library import tasks.
    """

    @staticmethod
    def calculate_total_steps(arguments_dict):
        """
        Get the number of in-progress steps in the import process, as shown in the UI.

        For reference, these are:

        1. Unpacking
        2. Verifying
        3. Updating
        """
        return 3

    @classmethod
    def generate_name(cls, arguments_dict):
        """
        Create a name for this particular import task instance.

        Arguments:
            arguments_dict (dict): The arguments given to the task function

        Returns:
            text_type: The generated name
        """
        key = arguments_dict[u'course_key_string']
        filename = arguments_dict[u'archive_name']
        return u'Import of {} from {}'.format(key, filename)


@task(base=CourseImportTask, bind=True)
def import_olx(self, user_id, course_key_string, archive_path, archive_name, language):
    """
    Import a course or library from a provided OLX .tar.gz archive.
    """
    courselike_key = CourseKey.from_string(course_key_string)
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        with respect_language(language):
            self.status.fail(_(u'Unknown User ID: {0}').format(user_id))
        return
    if not has_course_author_access(user, courselike_key):
        with respect_language(language):
            self.status.fail(_(u'Permission denied'))
        return

    is_library = isinstance(courselike_key, LibraryLocator)
    is_course = not is_library
    if is_library:
        root_name = LIBRARY_ROOT
        courselike_module = modulestore().get_library(courselike_key)
        import_func = import_library_from_xml
    else:
        root_name = COURSE_ROOT
        courselike_module = modulestore().get_course(courselike_key)
        import_func = import_course_from_xml

    # Locate the uploaded OLX archive (and download it from S3 if necessary)
    # Do everything in a try-except block to make sure everything is properly cleaned up.
    data_root = path(settings.GITHUB_REPO_ROOT)
    subdir = base64.urlsafe_b64encode(repr(courselike_key))
    course_dir = data_root / subdir
    try:
        self.status.set_state(u'Unpacking')

        if not archive_name.endswith(u'.tar.gz'):
            with respect_language(language):
                self.status.fail(_(u'We only support uploading a .tar.gz file.'))
                return

        temp_filepath = course_dir / get_valid_filename(archive_name)
        if not course_dir.isdir():
            os.mkdir(course_dir)

        LOGGER.debug(u'importing course to {0}'.format(temp_filepath))

        # Copy the OLX archive from where it was uploaded to (S3, Swift, file system, etc.)
        if not course_import_export_storage.exists(archive_path):
            LOGGER.info(u'Course import %s: Uploaded file %s not found', courselike_key, archive_path)
            with respect_language(language):
                self.status.fail(_(u'Tar file not found'))
            return
        with course_import_export_storage.open(archive_path, 'rb') as source:
            with open(temp_filepath, 'wb') as destination:
                def read_chunk():
                    """
                    Read and return a sequence of bytes from the source file.
                    """
                    return source.read(FILE_READ_CHUNK)
                for chunk in iter(read_chunk, b''):
                    destination.write(chunk)
        LOGGER.info(u'Course import %s: Download from storage complete', courselike_key)
        # Delete from source location
        course_import_export_storage.delete(archive_path)

        # If the course has an entrance exam then remove it and its corresponding milestone.
        # current course state before import.
        if is_course:
            if courselike_module.entrance_exam_enabled:
                fake_request = RequestFactory().get(u'/')
                fake_request.user = user
                from contentstore.views.entrance_exam import remove_entrance_exam_milestone_reference
                # TODO: Is this really ok?  Seems dangerous for a live course
                remove_entrance_exam_milestone_reference(fake_request, courselike_key)
                LOGGER.info(
                    u'entrance exam milestone content reference for course %s has been removed',
                    courselike_module.id
                )
    # Send errors to client with stage at which error occurred.
    except Exception as exception:  # pylint: disable=broad-except
        if course_dir.isdir():
            shutil.rmtree(course_dir)
            LOGGER.info(u'Course import %s: Temp data cleared', courselike_key)

        LOGGER.exception(u'Error importing course %s', courselike_key, exc_info=True)
        self.status.fail(text_type(exception))
        return

    # try-finally block for proper clean up after receiving file.
    try:
        tar_file = tarfile.open(temp_filepath)
        try:
            safetar_extractall(tar_file, (course_dir + u'/').encode(u'utf-8'))
        except SuspiciousOperation as exc:
            LOGGER.info(u'Course import %s: Unsafe tar file - %s', courselike_key, exc.args[0])
            with respect_language(language):
                self.status.fail(_(u'Unsafe tar file. Aborting import.'))
            return
        finally:
            tar_file.close()

        LOGGER.info(u'Course import %s: Uploaded file extracted', courselike_key)
        self.status.set_state(u'Verifying')
        self.status.increment_completed_steps()

        # find the 'course.xml' file
        def get_all_files(directory):
            """
            For each file in the directory, yield a 2-tuple of (file-name,
            directory-path)
            """
            for directory_path, _dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    yield (filename, directory_path)

        def get_dir_for_filename(directory, filename):
            """
            Returns the directory path for the first file found in the directory
            with the given name.  If there is no file in the directory with
            the specified name, return None.
            """
            for name, directory_path in get_all_files(directory):
                if name == filename:
                    return directory_path
            return None

        dirpath = get_dir_for_filename(course_dir, root_name)
        if not dirpath:
            with respect_language(language):
                self.status.fail(_(u'Could not find the {0} file in the package.').format(root_name))
                return

        dirpath = os.path.relpath(dirpath, data_root)
        LOGGER.debug(u'found %s at %s', root_name, dirpath)

        LOGGER.info(u'Course import %s: Extracted file verified', courselike_key)
        self.status.set_state(u'Updating')
        self.status.increment_completed_steps()

        with dog_stats_api.timer(
            u'courselike_import.time',
            tags=[u"courselike:{}".format(courselike_key)]
        ):
            courselike_items = import_func(
                modulestore(), user.id,
                settings.GITHUB_REPO_ROOT, [dirpath],
                load_error_modules=False,
                static_content_store=contentstore(),
                target_id=courselike_key
            )

        new_location = courselike_items[0].location
        LOGGER.debug(u'new course at %s', new_location)

        LOGGER.info(u'Course import %s: Course import successful', courselike_key)
    except Exception as exception:   # pylint: disable=broad-except
        LOGGER.exception(u'error importing course', exc_info=True)
        self.status.fail(text_type(exception))
    finally:
        if course_dir.isdir():
            shutil.rmtree(course_dir)
            LOGGER.info(u'Course import %s: Temp data cleared', courselike_key)

        if self.status.state == u'Updating' and is_course:
            # Reload the course so we have the latest state
            course = modulestore().get_course(courselike_key)
            if course.entrance_exam_enabled:
                entrance_exam_chapter = modulestore().get_items(
                    course.id,
                    qualifiers={u'category': u'chapter'},
                    settings={u'is_entrance_exam': True}
                )[0]

                metadata = {u'entrance_exam_id': text_type(entrance_exam_chapter.location)}
                CourseMetadata.update_from_dict(metadata, course, user) 
                from contentstore.views.entrance_exam import add_entrance_exam_milestone
                add_entrance_exam_milestone(course.id, entrance_exam_chapter)
                LOGGER.info(u'Course %s Entrance exam imported', course.id)
