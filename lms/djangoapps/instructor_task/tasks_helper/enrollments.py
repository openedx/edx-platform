"""
Instructor tasks related to enrollments.
"""

import json
import logging
from datetime import datetime
from time import time

from django.conf import settings
from django.contrib.sites.models import Site
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from edx_ace import ace
from edx_ace.recipient import Recipient
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.celery.task_utils import emulate_http_request
from openedx.core.lib.courses import get_course_by_id
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference
from django.utils.translation import gettext_lazy as _
from lms.djangoapps.instructor_analytics.basic import (
    enrolled_students_features,
    list_inactive_enrolled_students,
    list_may_enroll,
)

from common.djangoapps.student.models import CourseEnrollment  # lint-amnesty, pylint: disable=unused-import
from lms.djangoapps.instructor.utils.enrollment_utils import process_student_enrollment_batch as process_batch
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from lms.djangoapps.instructor_task.models import InstructorTask
from lms.djangoapps.instructor.message_types import BatchEnrollment

from .runner import TaskProgress
from .utils import upload_csv_to_report_store  # lint-amnesty, pylint: disable=unused-import

TASK_LOG = logging.getLogger('edx.celery.task')
FILTERED_OUT_ROLES = ['staff', 'instructor', 'finance_admin', 'sales_admin']


def upload_may_enroll_csv(_xblock_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    information about students who may enroll but have not done so
    yet, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about students who may enroll'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = task_input.get('features')
    student_data = list_may_enroll(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'may_enroll_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_inactive_enrolled_students_info_csv(_xblock_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    information about students who are enrolled in a course but have not
    activated their account yet, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about students who are enrolled and their account is inactive'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = task_input.get('features')
    student_data = list_inactive_enrolled_students(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'inactive_enrolled_students_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_students_csv(_xblock_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    current_step = {'step': 'Calculating Profile Info'}
    task_progress.update_task_state(extra_meta=current_step)

    # compute the student features table and format it
    query_features = task_input.get('features')
    student_data = enrolled_students_features(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_parent_dir = task_input.get('upload_parent_dir', '')
    upload_filename = task_input.get('filename', 'student_profile_info')
    upload_csv_to_report_store(rows, upload_filename, course_id, start_date, parent_dir=upload_parent_dir)

    return task_progress.update_task_state(extra_meta=current_step)


def process_student_enrollment_batch(_xblock_instance_args, _entry_id, course_id, task_input, action_name):
    """
    Process a batch of student enrollment/unenrollment operations asynchronously.

    Args:
        course_id: The course identifier
        task_input: Dictionary containing:
            - action: 'enroll' or 'unenroll'
            - identifiers: list of student identifiers (emails or usernames)
            - auto_enroll: boolean for auto-enrollment
            - email_students: boolean to send enrollment emails
            - reason: optional reason for enrollment change
            - secure: boolean indicating if request was secure (HTTPS)
        action_name: Name of the action being performed

    Returns:
        Task progress with results of enrollment operations
    """
    start_time = time()
    start_date = datetime.now(UTC)

    action = task_input.get("action")
    identifiers = task_input.get("identifiers", [])
    auto_enroll = task_input.get("auto_enroll", False)
    email_students = task_input.get("email_students", False)
    reason = task_input.get("reason")
    secure = task_input.get("secure", False)

    course_key = CourseKey.from_string(course_id) if isinstance(course_id, str) else course_id

    total_students = len(identifiers)
    task_progress = TaskProgress(action_name, total_students, start_time)

    current_step = {"step": f"Processing {action} operations for {total_students} students"}
    task_progress.update_task_state(extra_meta=current_step)

    def progress_callback(current, total, results):
        task_progress.attempted = current
        task_progress.succeeded = sum(1 for r in results if r.get("success", False))
        task_progress.failed = current - task_progress.succeeded

        # Update progress every 10 operations or at the end
        if current % 10 == 0 or current == total:
            current_step = {
                "step": f"Processed {current}/{total} {action} operations",
                "succeeded": task_progress.succeeded,
                "failed": task_progress.failed,
            }
            task_progress.update_task_state(extra_meta=current_step)

    batch_result = process_batch(
        course_key=course_key,
        action=action,
        identifiers=identifiers,
        auto_enroll=auto_enroll,
        email_students=email_students,
        reason=reason,
        secure=secure,
        progress_callback=progress_callback,
    )

    task_progress.attempted = batch_result["total_students"]
    task_progress.succeeded = batch_result["successful_operations"]
    task_progress.failed = batch_result["failed_operations"]
    task_progress.skipped = 0

    final_step = {
        "step": f"Completed {action} batch processing",
        "total_processed": batch_result["total_students"],
        "successful": batch_result["successful_operations"],
        "failed": batch_result["failed_operations"],
    }

    CSV_FIELDS = ["identifier", "success", "state_transition", "error_type"]
    CSV_DEFAULTS = {"identifier": "", "success": False, "state_transition": "", "error_type": ""}

    def extract_csv_row(result: dict) -> list[str]:
        """Extract CSV row data from result dictionary."""
        return [result.get(field, CSV_DEFAULTS[field]) for field in CSV_FIELDS]

    rows = [CSV_FIELDS] + [extract_csv_row(result) for result in batch_result["results"]]

    upload_csv_to_report_store(rows, "enrollment_batch_results", course_id, start_date)
    send_enrollment_task_completion_email(course_key, _entry_id, action, final_step)

    return task_progress.update_task_state(extra_meta=final_step)


def send_enrollment_task_completion_email(
    course_key: CourseKey, entry_id: int, action: str, task_result: dict
) -> None:
    """
    Send a completion email to the user who initiated the enrollment batch task using ACE framework.

    Args:
        course_key (CourseKey): The course key
        entry_id (int): The InstructorTask entry ID
        action (str): The action (e.g., 'enroll', 'unenroll')
        task_result (dict): Dictionary containing task completion results
    """
    try:
        instructor_task = InstructorTask.objects.get(pk=entry_id)
        requester = instructor_task.requester

        total_processed = task_result.get("total_processed", 0)
        successful = task_result.get("successful", 0)
        failed = task_result.get("failed", 0)

        action_name = _("enrollment") if action == "enroll" else _("unenrollment")

        course = get_course_by_id(course_key)
        course_name = course.display_name_with_default

        user_context = {
            "action_name": action_name,
            "course_name": course_name,
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "user_name": requester.get_full_name() or requester.username,
            "platform_name": settings.PLATFORM_NAME,
        }

        user_language = get_user_preference(requester, LANGUAGE_KEY)

        # Send email using ACE framework with proper context handling
        # We're in a Celery task context, so we need to emulate HTTP request
        site = Site.objects.get_current() if hasattr(Site.objects, "get_current") else None
        if not site:
            try:
                site = Site.objects.get(id=settings.SITE_ID)
            except Site.DoesNotExist:
                try:
                    site = Site.objects.first()
                except Exception:  # pylint: disable=broad-except
                    site = None

        site_name = configuration_helpers.get_value("SITE_NAME", settings.SITE_NAME)

        try:
            task_input = json.loads(instructor_task.task_input)
        except (json.JSONDecodeError, ValueError):
            task_input = {}

        secure = task_input.get("secure", True)
        protocol = "https" if secure else "http"
        course_url = f"{protocol}://{site_name}/courses/{course_key}/"
        user_context.update({"course_url": course_url})

        message = BatchEnrollment().personalize(
            recipient=Recipient(lms_user_id=requester.id, email_address=requester.email),
            language=user_language,
            user_context=user_context,
        )

        # Use emulate_http_request to provide the necessary context for ACE
        with emulate_http_request(site=site, user=requester):
            ace.send(message)

        TASK_LOG.info(
            "Enrollment task completion email sent via ACE to user %s (%s) for course %s. "
            "Action: %s, Results: %d successful, %d failed out of %d total",
            requester.username,
            requester.email,
            course_key,
            action,
            successful,
            failed,
            total_processed,
        )

    except InstructorTask.DoesNotExist:
        TASK_LOG.error("Could not send enrollment task completion email: InstructorTask with ID %s not found", entry_id)
    except Exception as exc:  # pylint: disable=broad-except
        TASK_LOG.exception("Failed to send enrollment task completion email for entry_id %s: %s", entry_id, str(exc))
