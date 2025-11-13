"""
Instructor tasks related to components and xblocks in the course.
"""

from datetime import datetime
from time import time
from pytz import UTC
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import modulestore

from .runner import TaskProgress
from .utils import upload_csv_to_report_store


def upload_xblock_list_csv(
    _xblock_instance_args, _entry_id, course_id, task_input, action_name
):
    """
    Generate a csv containing all components.
    """
    start_time = time()
    start_date = datetime.now(UTC)

    overviews = CourseOverview.objects.filter(id=course_id).order_by("id")
    # NOTE: if we want to report on all courses at once, use this line below instead of the one above
    # overviews = CourseOverview.objects.all().order_by('id')

    total_courses = overviews.count()
    task_progress = TaskProgress(action_name, total_courses, start_time)

    current_step = {"step": "Calculating XBlock Info"}
    task_progress.update_task_state(extra_meta=current_step)

    data = []
    succeeded_count = 0
    for overview in overviews:
        try:
            course = modulestore().get_course(overview.id)
            data.extend(
                {
                    "Course ID": course.id,
                    "Course Name": course.display_name,
                    "Section Name": section.display_name,
                    "Subsection Name": subsection.display_name,
                    "Unit Name": unit.display_name,
                    "Component Name": component.display_name,
                    "Xblock Type": component.location.block_type,
                }
                for section in course.get_children()
                for subsection in section.get_children()
                for unit in subsection.get_children()
                for component in unit.get_children()
            )
            succeeded_count += 1
        except:  # pylint: disable=bare-except
            print(f"FAILED GETTING COURSE {overview.id} FROM MODULESTORE")

    header, rows = format_dictlist(
        data,
        [
            "Course ID",
            "Course Name",
            "Section Name",
            "Subsection Name",
            "Unit Name",
            "Component Name",
            "Xblock Type",
        ],
    )

    task_progress.attempted = total_courses
    task_progress.succeeded = succeeded_count
    task_progress.skipped = task_progress.failed = total_courses - succeeded_count

    rows.insert(0, header)

    current_step = {"step": "Uploading CSV"}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_parent_dir = task_input.get("upload_parent_dir", "")
    upload_filename = task_input.get("filename", "xblocks_list")
    upload_csv_to_report_store(
        rows, upload_filename, course_id, start_date, parent_dir=upload_parent_dir
    )

    return task_progress.update_task_state(extra_meta=current_step)
