"""
This file contains celery tasks for contentstore views
"""

import base64
import json
import os
import shutil
import tarfile
from datetime import datetime
from tempfile import NamedTemporaryFile, mkdtemp

import olxcleaner
import pkg_resources
from ccx_keys.locator import CCXLocator
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from django.core.files import File
from django.test import RequestFactory
from django.utils.text import get_valid_filename
from edx_django_utils.monitoring import (
    set_code_owner_attribute,
    set_code_owner_attribute_from_module,
    set_custom_attribute,
    set_custom_attributes_for_course_key
)
from olxcleaner.exceptions import ErrorLevel
from olxcleaner.reporting import report_error_summary, report_errors
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator
from organizations.api import add_organization_course, ensure_organization
from organizations.models import OrganizationCourse
from path import Path as path
from pytz import UTC
from user_tasks.models import UserTaskArtifact, UserTaskStatus
from user_tasks.tasks import UserTask

import cms.djangoapps.contentstore.errors as UserErrors
from cms.djangoapps.contentstore.courseware_index import (
    CoursewareSearchIndexer,
    LibrarySearchIndexer,
    SearchIndexingError
)
from cms.djangoapps.contentstore.storage import course_import_export_storage
from cms.djangoapps.contentstore.utils import initialize_permissions, reverse_usage_url, translation_language
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from common.djangoapps.course_action_state.models import CourseRerunState
from common.djangoapps.student.auth import has_course_author_access
from common.djangoapps.util.monitoring import monitor_import_failure
from openedx.core.djangoapps.content.learning_sequences.api import key_supports_outlines
from openedx.core.djangoapps.course_apps.toggles import exams_ida_enabled
from openedx.core.djangoapps.discussions.tasks import update_unit_discussion_state_from_discussion_blocks
from openedx.core.djangoapps.embargo.models import CountryAccessRule, RestrictedCourse
from openedx.core.lib.extract_tar import safetar_extractall
from xmodule.contentstore.django import contentstore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.course_block import CourseFields  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.exceptions import SerializationError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import COURSE_ROOT, LIBRARY_ROOT  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import DuplicateCourseError, InvalidProctoringProvider, ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.xml_exporter import export_course_to_xml, export_library_to_xml  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.xml_importer import CourseImportException, import_course_from_xml, import_library_from_xml  # lint-amnesty, pylint: disable=wrong-import-order

from .outlines import update_outline_from_modulestore
from .outlines_regenerate import CourseOutlineRegenerate
from .toggles import bypass_olx_failure_enabled
from .utils import course_import_olx_validation_is_enabled

User = get_user_model()

LOGGER = get_task_logger(__name__)
FILE_READ_CHUNK = 1024  # bytes
FULL_COURSE_REINDEX_THRESHOLD = 1
ALL_ALLOWED_XBLOCKS = frozenset(
    [entry_point.name for entry_point in pkg_resources.iter_entry_points("xblock.v1")]
)


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

    for field, value in field_values.items():
        setattr(instance, field, value)

    instance.save()

    return instance


@shared_task
@set_code_owner_attribute
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

        update_unit_discussion_state_from_discussion_blocks(destination_course_key, user_id)

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

        org_data = ensure_organization(source_course_key.org)
        add_organization_course(org_data, destination_course_key)
        return "succeeded"

    except DuplicateCourseError:
        # do NOT delete the original course, only update the status
        CourseRerunState.objects.failed(course_key=destination_course_key)
        LOGGER.exception('Course Rerun Error')
        return "duplicate course"

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        CourseRerunState.objects.failed(course_key=destination_course_key)
        LOGGER.exception('Course Rerun Error')

        try:
            # cleanup any remnants of the course
            modulestore().delete_course(destination_course_key, user_id)
        except ItemNotFoundError:
            # it's possible there was an error even before the course block was created
            pass

        return "exception: " + str(exc)


def deserialize_fields(json_fields):
    fields = json.loads(json_fields)
    for field_name, value in fields.items():
        fields[field_name] = getattr(CourseFields, field_name).from_json(value)
    return fields


def _parse_time(time_isoformat):
    """ Parses time from iso format """
    return datetime.strptime(
        # remove the +00:00 from the end of the formats generated within the system
        time_isoformat.split('+')[0],
        "%Y-%m-%dT%H:%M:%S.%f"
    ).replace(tzinfo=UTC)


@shared_task
@set_code_owner_attribute
def update_search_index(course_id, triggered_time_isoformat):
    """ Updates course search index. """
    try:
        course_key = CourseKey.from_string(course_id)

        # We skip search indexing for CCX courses because there is currently
        # some issue around Modulestore caching that makes it prohibitively
        # expensive (sometimes hours-long for really complex courses).
        if isinstance(course_key, CCXLocator):
            LOGGER.warning(
                'Search indexing skipped for CCX Course %s (this is currently too slow to run in production)',
                course_id
            )
            return

        CoursewareSearchIndexer.index(modulestore(), course_key, triggered_at=(_parse_time(triggered_time_isoformat)))

    except SearchIndexingError as exc:
        error_list = exc.error_list
        LOGGER.error(
            "Search indexing error for complete course %s - %s - %s",
            course_id,
            str(exc),
            error_list,
        )
    else:
        LOGGER.debug('Search indexing successful for complete course %s', course_id)


@shared_task
@set_code_owner_attribute
def update_library_index(library_id, triggered_time_isoformat):
    """ Updates course search index. """
    try:
        library_key = CourseKey.from_string(library_id)
        LibrarySearchIndexer.index(modulestore(), library_key, triggered_at=(_parse_time(triggered_time_isoformat)))

    except SearchIndexingError as exc:
        LOGGER.error('Search indexing error for library %s - %s', library_id, str(exc))
    else:
        LOGGER.debug('Search indexing successful for library %s', library_id)


@shared_task
@set_code_owner_attribute
def update_special_exams_and_publish(course_key_str):
    """
    Registers special exams for a given course and calls publishing flow.

    on_course_publish expects that the edx-proctoring subsystem has been refreshed
    before being executed, so both functions are called here synchronously.
    """
    from cms.djangoapps.contentstore.exams import register_exams
    from cms.djangoapps.contentstore.proctoring import register_special_exams as register_exams_legacy
    from openedx.core.djangoapps.credit.signals import on_course_publish

    course_key = CourseKey.from_string(course_key_str)
    LOGGER.info('Attempting to register exams for course %s', course_key_str)

    # Call the appropriate handler for either the exams IDA or the edx-proctoring plugin
    register_exams_handler = register_exams if exams_ida_enabled(course_key) else register_exams_legacy
    try:
        register_exams_handler(course_key)
        LOGGER.info('Successfully registered exams for course %s', course_key_str)
    # pylint: disable=broad-except
    except Exception as exception:
        LOGGER.exception(exception)

    LOGGER.info('Publishing course %s', course_key_str)
    on_course_publish(course_key)


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
        key = arguments_dict['course_key_string']
        return f'Export of {key}'


@shared_task(base=CourseExportTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
def export_olx(self, user_id, course_key_string, language):
    """
    Export a course or library to an OLX .tar.gz archive and prepare it for download.
    """
    set_code_owner_attribute_from_module(__name__)
    courselike_key = CourseKey.from_string(course_key_string)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        with translation_language(language):
            self.status.fail(UserErrors.UNKNOWN_USER_ID.format(user_id))
        return
    if not has_course_author_access(user, courselike_key):
        with translation_language(language):
            self.status.fail(UserErrors.PERMISSION_DENIED)
        return

    if isinstance(courselike_key, LibraryLocator):
        courselike_block = modulestore().get_library(courselike_key)
    else:
        courselike_block = modulestore().get_course(courselike_key)

    try:
        self.status.set_state('Exporting')
        tarball = create_export_tarball(courselike_block, courselike_key, {}, self.status)
        artifact = UserTaskArtifact(status=self.status, name='Output')
        artifact.file.save(name=os.path.basename(tarball.name), content=File(tarball))
        artifact.save()
    # catch all exceptions so we can record useful error messages
    except Exception as exception:  # pylint: disable=broad-except
        LOGGER.exception('Error exporting course %s', courselike_key, exc_info=True)
        if self.status.state != UserTaskStatus.FAILED:
            self.status.fail({'raw_error_msg': str(exception)})
        return


def create_export_tarball(course_block, course_key, context, status=None):
    """
    Generates the export tarball, or returns None if there was an error.

    Updates the context with any error information if applicable.
    """
    name = course_block.url_name
    export_file = NamedTemporaryFile(prefix=name + '.',
                                     suffix=".tar.gz")  # lint-amnesty, pylint: disable=consider-using-with
    root_dir = path(mkdtemp())

    try:
        if isinstance(course_key, LibraryLocator):
            export_library_to_xml(modulestore(), contentstore(), course_key, root_dir, name)
        else:
            export_course_to_xml(modulestore(), contentstore(), course_block.id, root_dir, name)

        if status:
            status.set_state('Compressing')
            status.increment_completed_steps()
        LOGGER.debug('tar file being generated at %s', export_file.name)
        with tarfile.open(name=export_file.name, mode='w:gz') as tar_file:
            tar_file.add(root_dir / name, arcname=name)

    except SerializationError as exc:
        LOGGER.exception('There was an error exporting %s', course_key, exc_info=True)
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
        key = arguments_dict['course_key_string']
        filename = arguments_dict['archive_name']
        return f'Import of {key} from {filename}'


@shared_task(base=CourseImportTask, bind=True)
# Note: The decorator @set_code_owner_attribute cannot be used here because the UserTaskMixin
#   does stack inspection and can't handle additional decorators.
# lint-amnesty, pylint: disable=too-many-statements
def import_olx(self, user_id, course_key_string, archive_path, archive_name, language):
    """
    Import a course or library from a provided OLX .tar.gz archive.
    """
    set_code_owner_attribute_from_module(__name__)
    current_step = 'Unpacking'
    courselike_key = CourseKey.from_string(course_key_string)
    set_custom_attributes_for_course_key(courselike_key)
    log_prefix = f'Course import {courselike_key}'
    self.status.set_state(current_step)

    data_root = path(settings.GITHUB_REPO_ROOT)
    subdir = base64.urlsafe_b64encode(repr(courselike_key).encode('utf-8')).decode('utf-8')
    course_dir = data_root / subdir

    def validate_user():
        """Validate if the user exists otherwise log error. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist as exc:
            with translation_language(language):
                self.status.fail(UserErrors.USER_PERMISSION_DENIED)
            LOGGER.error(f'{log_prefix}: Unknown User: {user_id}')
            monitor_import_failure(courselike_key, current_step, exception=exc)
            return

    def user_has_access(user):
        """Return True if user has studio write access to the given course."""
        has_access = has_course_author_access(user, courselike_key)
        if not has_access:
            message = f'User permission denied: {user.username}'
            with translation_language(language):
                self.status.fail(UserErrors.COURSE_PERMISSION_DENIED)
            LOGGER.error(f'{log_prefix}: {message}')
            monitor_import_failure(courselike_key, current_step, message=message)
        return has_access

    def file_is_supported():
        """Check if it is a supported file."""
        file_is_valid = archive_name.endswith('.tar.gz')

        if not file_is_valid:
            message = f'Unsupported file {archive_name}'
            with translation_language(language):
                self.status.fail(UserErrors.INVALID_FILE_TYPE)
            LOGGER.error(f'{log_prefix}: {message}')
            monitor_import_failure(courselike_key, current_step, message=message)
        return file_is_valid

    def file_exists_in_storage():
        """Verify archive path exists in storage."""
        archive_path_exists = course_import_export_storage.exists(archive_path)

        if not archive_path_exists:
            message = f'Uploaded file {archive_path} not found'
            with translation_language(language):
                self.status.fail(UserErrors.FILE_NOT_FOUND)
            LOGGER.error(f'{log_prefix}: {message}')
            monitor_import_failure(courselike_key, current_step, message=message)
        return archive_path_exists

    def verify_root_name_exists(course_dir, root_name):
        """Verify root xml file exists."""

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
            message = UserErrors.FILE_MISSING.format(root_name)
            with translation_language(language):
                self.status.fail(message)
            LOGGER.error(f'{log_prefix}: {message}')
            monitor_import_failure(courselike_key, current_step, message=message)
            return
        return dirpath

    user = validate_user()
    if not user:
        return

    if not user_has_access(user):
        return

    if not file_is_supported():
        return

    is_library = isinstance(courselike_key, LibraryLocator)
    is_course = not is_library
    if is_library:
        root_name = LIBRARY_ROOT
        courselike_block = modulestore().get_library(courselike_key)
        import_func = import_library_from_xml
    else:
        root_name = COURSE_ROOT
        courselike_block = modulestore().get_course(courselike_key)
        import_func = import_course_from_xml

    # Locate the uploaded OLX archive (and download it from S3 if necessary)
    # Do everything in a try-except block to make sure everything is properly cleaned up.
    try:
        LOGGER.info(f'{log_prefix}: unpacking step started')

        temp_filepath = course_dir / get_valid_filename(archive_name)
        if not course_dir.isdir():
            os.mkdir(course_dir)

        LOGGER.info(f'{log_prefix}: importing course to {temp_filepath}')

        # Copy the OLX archive from where it was uploaded to (S3, Swift, file system, etc.)
        if not file_exists_in_storage():
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

        LOGGER.info(f'{log_prefix}: Download from storage complete')
        # Delete from source location
        course_import_export_storage.delete(archive_path)

        # If the course has an entrance exam then remove it and its corresponding milestone.
        # current course state before import.
        if is_course:
            if courselike_block.entrance_exam_enabled:
                fake_request = RequestFactory().get('/')
                fake_request.user = user
                from .views.entrance_exam import remove_entrance_exam_milestone_reference
                # TODO: Is this really ok?  Seems dangerous for a live course
                remove_entrance_exam_milestone_reference(fake_request, courselike_key)
                LOGGER.info(f'{log_prefix}: entrance exam milestone content reference has been removed')
    # Send errors to client with stage at which error occurred.
    except Exception as exception:  # pylint: disable=broad-except
        if course_dir.isdir():
            shutil.rmtree(course_dir)
            LOGGER.info(f'{log_prefix}: Temp data cleared')

        self.status.fail(UserErrors.UNKNOWN_ERROR_IN_UNPACKING)
        LOGGER.exception(f'{log_prefix}: Unknown error while unpacking', exc_info=True)
        monitor_import_failure(courselike_key, current_step, exception=exception)
        return

    # try-finally block for proper clean up after receiving file.
    try:
        tar_file = tarfile.open(temp_filepath)  # lint-amnesty, pylint: disable=consider-using-with
        try:
            safetar_extractall(tar_file, (course_dir + '/'))
        except SuspiciousOperation as exc:
            with translation_language(language):
                self.status.fail(UserErrors.UNSAFE_TAR_FILE)
            LOGGER.error(f'{log_prefix}: Unsafe tar file')
            monitor_import_failure(courselike_key, current_step, exception=exc)
            return
        finally:
            tar_file.close()

        current_step = 'Verifying'
        self.status.set_state(current_step)
        self.status.increment_completed_steps()
        LOGGER.info(f'{log_prefix}: Uploaded file extracted. Verification step started')

        dirpath = verify_root_name_exists(course_dir, root_name)
        if not dirpath:
            return

        if not validate_course_olx(courselike_key, dirpath, self.status):
            return

        dirpath = os.path.relpath(dirpath, data_root)

        current_step = 'Updating'
        self.status.set_state(current_step)
        self.status.increment_completed_steps()
        LOGGER.info(f'{log_prefix}: Extracted file verified. Updating course started')

        courselike_items = import_func(
            modulestore(), user.id,
            settings.GITHUB_REPO_ROOT, [dirpath],
            load_error_blocks=False,
            static_content_store=contentstore(),
            target_id=courselike_key,
            verbose=True,
        )

        new_location = courselike_items[0].location
        LOGGER.debug('new course at %s', new_location)

        LOGGER.info(f'{log_prefix}: Course import successful')
        set_custom_attribute('course_import_completed', True)
    except (CourseImportException, InvalidProctoringProvider, DuplicateCourseError) as known_exe:
        handle_course_import_exception(courselike_key, known_exe, self.status)
    except Exception as exception:  # pylint: disable=broad-except
        handle_course_import_exception(courselike_key, exception, self.status, known=False)
    finally:
        if course_dir.isdir():
            shutil.rmtree(course_dir)
            LOGGER.info(f'{log_prefix}: Temp data cleared')

        if self.status.state == 'Updating' and is_course:
            # Reload the course so we have the latest state
            course = modulestore().get_course(courselike_key)
            if course.entrance_exam_enabled:
                entrance_exam_chapter = modulestore().get_items(
                    course.id,
                    qualifiers={'category': 'chapter'},
                    settings={'is_entrance_exam': True}
                )[0]

                metadata = {'entrance_exam_id': str(entrance_exam_chapter.location)}
                CourseMetadata.update_from_dict(metadata, course, user)
                from .views.entrance_exam import add_entrance_exam_milestone
                add_entrance_exam_milestone(course.id, entrance_exam_chapter)
                LOGGER.info(f'Course import {course.id}: Entrance exam imported')


@shared_task
@set_code_owner_attribute
def update_all_outlines_from_modulestore_task():
    """
    Celery task that creates multiple celery tasks - one per learning_sequence course outline
    to regenerate. The list of course keys to regenerate comes from the proxy model itself.
    """
    course_key_list = [str(course_key) for course_key in CourseOutlineRegenerate.get_course_outline_ids()]
    for course_key_str in course_key_list:
        try:
            course_key = CourseKey.from_string(course_key_str)
            if not key_supports_outlines(course_key):
                LOGGER.warning(
                    (
                        "update_multiple_outlines_from_modulestore_task called for course key"
                        " %s, which does not support learning_sequence outlines."
                    ),
                    course_key_str
                )
                continue

            update_outline_from_modulestore_task.delay(course_key_str)
        except Exception:  # pylint: disable=broad-except
            # Swallow the exception to continue the loop through course keys - but log it.
            LOGGER.exception("Could not create course outline for course %s", course_key_str)


@shared_task
@set_code_owner_attribute
def update_outline_from_modulestore_task(course_key_str: str):
    """
    Celery task that creates a learning_sequence course outline.
    """
    try:
        course_key = CourseKey.from_string(course_key_str)
        if not key_supports_outlines(course_key):
            LOGGER.warning(
                (
                    "update_outline_from_modulestore_task called for course key"
                    " %s, which does not support learning_sequence outlines."
                ),
                course_key_str
            )
            return

        update_outline_from_modulestore(course_key)
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Could not create course outline for course %s", course_key_str)
        raise  # Re-raise so that errors are noted in reporting.


def validate_course_olx(courselike_key, course_dir, status):
    """
    Validates course olx and records the errors as an artifact.

    Arguments:
        courselike_key: A locator identifies a course resource.
        course_dir: complete path to the course olx
        status: UserTaskStatus object.
    """
    olx_is_valid = True
    log_prefix = f'Course import {courselike_key}'
    validation_failed_mesg = 'CourseOlx validation failed.'
    is_library = isinstance(courselike_key, LibraryLocator)

    if is_library:
        return olx_is_valid

    if not course_import_olx_validation_is_enabled():
        return olx_is_valid
    try:
        __, errorstore, __ = olxcleaner.validate(
            filename=course_dir,
            steps=settings.COURSE_OLX_VALIDATION_STAGE,
            ignore=settings.COURSE_OLX_VALIDATION_IGNORE_LIST,
            allowed_xblocks=ALL_ALLOWED_XBLOCKS
        )
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception(f'{log_prefix}: CourseOlx could not be validated')
        return olx_is_valid

    has_errors = errorstore.return_error(ErrorLevel.ERROR.value)
    if not has_errors:
        return olx_is_valid

    LOGGER.error(f'{log_prefix}: {validation_failed_mesg}')
    log_errors_to_artifact(errorstore, status)

    if bypass_olx_failure_enabled():
        return olx_is_valid

    monitor_import_failure(courselike_key, status.state, message=validation_failed_mesg)
    status.fail(UserErrors.OLX_VALIDATION_FAILED)
    return False


def log_errors_to_artifact(errorstore, status):
    """Log errors as a task artifact."""

    def get_error_by_type(error_type):
        return [error for error in error_report if error.startswith(error_type)]

    error_summary = report_error_summary(errorstore)
    error_report = report_errors(errorstore)
    message = json.dumps({
        'summary': error_summary,
        'errors': get_error_by_type(ErrorLevel.ERROR.name),
        'warnings': get_error_by_type(ErrorLevel.WARNING.name),
    })
    UserTaskArtifact.objects.create(status=status, name='OLX_VALIDATION_ERROR', text=message)


def handle_course_import_exception(courselike_key, exception, status, known=True):
    """
    Handle course import exception and fail task status.

    Arguments:
        courselike_key: A locator identifies a course resource.
        exception: Exception object
        status: UserTaskStatus object.
        known: boolean indicating if this is a known failure or unknown.
    """
    exception_message = str(exception)
    log_prefix = f"Course import {courselike_key}:"
    LOGGER.exception(f"{log_prefix} Error while importing course: {exception_message}")
    task_fail_message = UserErrors.UNKNOWN_ERROR_IN_IMPORT
    monitor_import_failure(courselike_key, status.state, exception=exception)

    if known:
        task_fail_message = exception_message

    if status.state != UserTaskStatus.FAILED:
        status.fail(task_fail_message)
