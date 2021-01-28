"""
This file contains celery tasks for contentstore views
"""
import beeline
import logging
import requests
import os
import tarfile
import datetime

from tempfile import NamedTemporaryFile, TemporaryDirectory

from celery.task import task
from celery.utils.log import get_task_logger

from django.db import transaction
from django.conf import settings

from student.models import CourseEnrollment
from student.roles import CourseAccessRole

from opaque_keys.edx.keys import CourseKey

from organizations.models import Organization, OrganizationCourse
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.xml_importer import import_course_from_xml

LOGGER = get_task_logger(__name__)


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
    try:
        organization = Organization.objects.get(pk=organization_id)

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

        # Build the GitHub download URL from settings to download the course in tar.gz format
        # from the GitHub releases
        course_download_url = 'https://github.com/{}/{}/archive/{}.tar.gz'.format(
            course_github_org,
            course_github_name,
            course_version,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception('Course Clone Error')
        return 'exception: ' + str(exc)

    try:
        # Download the course in tar.gz format from github in a temp. file using a random file name
        with TemporaryDirectory() as dir_name, NamedTemporaryFile() as temp_file:
            response = requests.get(course_download_url)
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

            # TODO: Remove this once we roll out Tahoe 2.0 sites, because OrgStaffRole is implemented there.
            # Add the new registered user as admin in the course
            CourseAccessRole.objects.get_or_create(
                # TODO: Ensure only an admin get this course (`is_amc_admin`).
                user=organization.users.first(),
                role='instructor',  # This is called "Course Admin" in Studio.
                course_id=course_target_id,
                org=organization.short_name
            )

            OrganizationCourse.objects.create(
                organization=organization,
                course_id=str(course_target_id),
                active=True
            )

            SignalHandler.course_published.send(
                sender=__name__,
                course_key=course_target_id,
            )

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        logging.exception('Course Clone Error')

        try:
            # cleanup any remnants of the course
            modulestore().delete_course(course_target_id, ModuleStoreEnum.UserID.system)
        except ItemNotFoundError:
            # it's possible there was an error even before the course module was created
            pass

        return 'exception: ' + str(exc)

    try:
        # enroll the user in the course
        # we use a separate try/except because we want to keep the course even
        # if the user cannot be enrolled, because it will find the course anyway
        CourseEnrollment.enroll(
            organization.users.first(),
            course_target_id,
            'honor'
        )
        # Regenerate course overview to properly display it in the home page.
        CourseOverview.update_select_courses([course_target_id], force_update=True)
    except Exception as exc:
        logging.exception('Error enrolling the user in default course')
        return 'exception: ' + str(exc)
