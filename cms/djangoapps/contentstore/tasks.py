"""
This file contains celery tasks for contentstore views
"""
from __future__ import absolute_import

import base64
import json
import logging
import os
import shutil
import tarfile
from datetime import datetime

from celery.task import task
from celery.utils.log import get_task_logger
from path import Path as path
from pytz import UTC
from six import iteritems, text_type

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory
from django.utils.text import get_valid_filename
from django.utils.translation import ugettext as _

from djcelery.common import respect_language
from user_tasks.tasks import UserTask

import dogstats_wrapper as dog_stats_api
from contentstore.courseware_index import CoursewareSearchIndexer, LibrarySearchIndexer, SearchIndexingError
from contentstore.storage import course_import_export_storage
from contentstore.utils import initialize_permissions
from course_action_state.models import CourseRerunState
from models.settings.course_metadata import CourseMetadata
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator
from openedx.core.lib.extract_tar import safetar_extractall
from student.auth import has_course_author_access
from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseFields
from xmodule.modulestore import COURSE_ROOT, LIBRARY_ROOT
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError
from xmodule.modulestore.xml_importer import import_course_from_xml, import_library_from_xml


LOGGER = get_task_logger(__name__)
FILE_READ_CHUNK = 1024  # bytes
FULL_COURSE_REINDEX_THRESHOLD = 1


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

        return "succeeded"

    except DuplicateCourseError:
        # do NOT delete the original course, only update the status
        CourseRerunState.objects.failed(course_key=destination_course_key)
        logging.exception(u'Course Rerun Error')
        return "duplicate course"

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        CourseRerunState.objects.failed(course_key=destination_course_key)
        logging.exception(u'Course Rerun Error')

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

        Note that the task does a little cleanup work after ``completed_steps``
        reaches its final value, so the task isn't truly finished until the
        ``state`` field becomes "Succeeded".
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
        if not course_dir.isdir():  # pylint: disable=no-value-for-parameter
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
        if course_dir.isdir():  # pylint: disable=no-value-for-parameter
            shutil.rmtree(course_dir)
            LOGGER.info(u'Course import %s: Temp data cleared', courselike_key)

        LOGGER.exception(u'Error importing course %s', courselike_key)
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
        self.status.increment_completed_steps()
    except Exception as exception:   # pylint: disable=broad-except
        LOGGER.exception(u'error importing course')
        self.status.fail(text_type(exception))
    finally:
        if course_dir.isdir():  # pylint: disable=no-value-for-parameter
            shutil.rmtree(course_dir)
            LOGGER.info(u'Course import %s: Temp data cleared', courselike_key)

        if self.status.completed_steps == 3 and is_course:
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
