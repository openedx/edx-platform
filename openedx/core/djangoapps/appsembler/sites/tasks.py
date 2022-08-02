"""
This file contains celery tasks for contentstore views
"""
import beeline
import requests
import os
import tarfile
import datetime

from tempfile import NamedTemporaryFile, TemporaryDirectory

from celery.task import task
from celery.utils.log import get_task_logger

from django.db import transaction
from django.conf import settings

from opaque_keys.edx.keys import CourseKey

from organizations.models import Organization, OrganizationCourse
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.xml_importer import import_course_from_xml

log = get_task_logger(__name__)


def current_year():
    """
    A helper to get current year.
    """
    return datetime.datetime.now().year


def import_course_on_site_creation_after_transaction(organization):
    """
    Clone the course after Database transaction is committed, only if the import feature is enabled.

    :param organization: Organization to create the course for.
    :return bool: Whether the course is scheduled for creation or not.
    """
    if settings.FEATURES.get("APPSEMBLER_IMPORT_DEFAULT_COURSE_ON_SITE_CREATION", False):
        beeline.add_context_field("default_course_on_site_creation_flag", True)

        def import_task_on_commit():
            """
            Run the import task after the commit to avoid Organization.DoesNotExist error on the Celery.
            """
            import_course_on_site_creation_apply_async(organization)

        transaction.on_commit(import_task_on_commit)
        return True

    return False


def import_course_on_site_creation_apply_async(organization):
    """
    Apply the `import_course_on_site_creation` task async. with proper call and configurations.

    This helper ensures that the configuration is tested properly even if
    the `RegistrationSerializer` has no tests.

    :param organization:
    :return: ResultBase.
    """
    return import_course_on_site_creation.apply_async(
        kwargs={'organization_id': organization.id},
        retry=False,  # The task is not expected to be able to recover after a failure.
    )


@task()
def import_course_on_site_creation(organization_id):
    """
    Celery task to copy the template course for new sites.

    :param organization_id: The integer ID for the organization object in database.
    """
    log.info('Starting importing course for organization_id %s', organization_id)
    try:
        organization = Organization.objects.get(pk=organization_id)
        log.info('Importing course for organization %s', organization)

        course_name = settings.TAHOE_DEFAULT_COURSE_NAME
        course_github_org = settings.TAHOE_DEFAULT_COURSE_GITHUB_ORG
        course_github_name = settings.TAHOE_DEFAULT_COURSE_GITHUB_NAME
        course_version = settings.TAHOE_DEFAULT_COURSE_VERSION

        # Create the course key object with the current created rganization, the course
        # name from the settings and the current year
        course_target_id = CourseKey.from_string(
            'course-v1:{}+{}+{}'.format(
                organization.short_name,
                course_name,
                current_year(),
            )
        )
        log.info('Importing course for organization %s with course_id %s',
                 organization, course_target_id)

        # Build the GitHub download URL from settings to download the course in tar.gz format
        # from the GitHub releases
        course_download_url = 'https://github.com/{}/{}/archive/{}.tar.gz'.format(
            course_github_org,
            course_github_name,
            course_version,
        )
    except Exception as exc:  # pylint: disable=broad-except
        log.exception('Course Clone Error')
        return 'exception: ' + str(exc)

    try:
        # Download the course in tar.gz format from github in a temp. file using a random file name
        with TemporaryDirectory() as dir_name, NamedTemporaryFile() as temp_file:
            log.info('Importing course for organization %s with url %s', organization, course_download_url)
            response = requests.get(course_download_url)
            log.info('Downloaded course for organization %s with url %s', organization, course_download_url)
            file_path = temp_file.name
            with open(file_path, 'wb') as fd:
                for chunk in response.iter_content(chunk_size=128):
                    fd.write(chunk)

            # untar the downloaded file in the temp. directory just created
            with tarfile.open(file_path) as tar:
                extracted_course_folder = tar.getnames()[0]
                tar.extractall(path=dir_name)

            # Import the course
            m_store = modulestore()
            import_course_from_xml(
                m_store,
                ModuleStoreEnum.UserID.system,
                os.path.join(dir_name, extracted_course_folder),
                source_dirs=[os.path.join(dir_name, extracted_course_folder, 'course')],
                static_content_store=contentstore(),
                target_id=course_target_id,
                create_if_not_present=True,
            )
            log.info('Imported course for organization %s')

            OrganizationCourse.objects.create(
                organization=organization,
                course_id=str(course_target_id),
                active=True
            )

            SignalHandler.course_published.send(
                sender=__name__,
                course_key=course_target_id,
            )
            emit_course_published_signal_in_cms.apply_async(
                kwargs={'course_key': str(course_target_id)},
                countdown=settings.TAHOE_DEFAULT_COURSE_CMS_TASK_DELAY,  # Delay the "course_published" signal
                routing_key=settings.CMS_UPDATE_SEARCH_INDEX_JOB_QUEUE,  # Schedule in CMS
            )
            log.info('course_published import signal emitted for course %s', course_target_id)

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        log.exception('Course Clone Error')

        try:
            # cleanup any remnants of the course
            log.info('Deleting tahoe welcome course %s', course_target_id)
            modulestore().delete_course(course_target_id, ModuleStoreEnum.UserID.system)
            log.info('Deleted tahoe welcome course %s', course_target_id)
        except ItemNotFoundError:
            # it's possible there was an error even before the course module was created
            pass

        return 'exception: ' + str(exc)


@task()
def emit_course_published_signal_in_cms(course_key):
    """
    An LMS-scheduled task to update CMS course search index and other tasks.

    This is a "routing" task to schedule the `update_search_index` task from _LMS_ and run it in the _CMS_ queue among
    other tasks.

    This is to work around the `cms.djangoapps.contentstore` module cannot be imported from LMS code.
    """
    from cms.djangoapps.contentstore.signals import handlers  # Local import that run only in CMS.

    handlers.listen_for_course_publish(
        sender=__name__,
        course_key=CourseKey.from_string(course_key),
    )
