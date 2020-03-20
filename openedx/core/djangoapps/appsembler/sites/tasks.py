"""
This file contains celery tasks for contentstore views
"""
import os
import logging
import requests
import uuid
import os
import tarfile
import shutil
import datetime

from backports import tempfile

from celery.task import task
from celery.utils.log import get_task_logger

from django.conf import settings

from student.roles import CourseAccessRole

from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey

from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError, ItemNotFoundError
from xmodule.modulestore.xml_importer import import_course_from_xml

LOGGER = get_task_logger(__name__)
FULL_COURSE_REINDEX_THRESHOLD = 1


@task()
def import_course_on_site_creation(organization):
    """
    Reruns a course in a new celery task.
    """
    try:
        course_name = settings.TAHOE_DEFAULT_COURSE_NAME
        course_github_org = settings.TAHOE_DEFAULT_COURSE_GITHUB_ORG
        course_github_name = settings.TAHOE_DEFAULT_COURSE_GITHUB_NAME
        course_version = settings.TAHOE_DEFAULT_COURSE_VERSION

        # build the github download URL from settings to download the course
        # in tar.gz format from the github releases
        course_download_url = 'https://github.com/{}/{}/archive/{}.tar.gz'.format(
            course_github_org,
            course_github_name,
            course_version
        )

        # download the course in tar.gz format from github in /tmp using a
        # random file name
        with tempfile.TemporaryDirectory() as dir:
            r = requests.get(course_download_url)
            course_file_name = str(uuid.uuid4()) + ".tar.gz"
            file_path = os.path.join("/", "tmp", course_file_name)
            with open(file_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=128):
                    fd.write(chunk)

            # untar the downloaded file in the /tmp/random_dir just created
            with tarfile.open(file_path) as tar:
                extracted_course_folder = tar.getnames()[0]
                tar.extractall(path=dir)

            # create the course key object with the current created
            # organization, the course name from the settings and the current
            # year
            course_target_id = CourseKey.from_string(
                'course-v1:{}+{}+{}'.format(
                    organization.short_name,
                    course_name,
                    str(datetime.datetime.now().year)
                )
            )

            # import the course
            mstore = modulestore()
            course_items = import_course_from_xml(
                mstore,
                ModuleStoreEnum.UserID.mgmt_command,
                os.path.join(dir, extracted_course_folder),
                source_dirs=os.path.join(dir, extracted_course_folder, 'course'),
                target_id=course_target_id,
                create_if_not_present=True,
            )

            # remove the course file
            os.remove(file_path)

            # add the new registered user as admin in the course
            access_role, created = CourseAccessRole.objects.get_or_create(
                user=organization.users.first(),
                role="instructor",
                course_id=course_target_id,
                org=organization.short_name
            )

    # catch all exceptions so we can update the state and properly cleanup the course.
    except Exception as exc:  # pylint: disable=broad-except
        # update state: Failed
        logging.exception(u'Course Clone Error')

        try:
            # cleanup any remnants of the course
            modulestore().delete_course(course_target_id, organization.users.first())
        except ItemNotFoundError:
            # it's possible there was an error even before the course module was created
            pass

        return "exception: " + unicode(exc)
