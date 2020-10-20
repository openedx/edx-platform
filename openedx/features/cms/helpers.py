"""
Helper methods for CMS application
"""
from dateutil.parser import parse
from django.contrib.auth.models import User
from opaque_keys.edx.keys import CourseKey
from openassessment.xblock.defaults import DEFAULT_DUE, DEFAULT_START
from pytz import utc

from course_action_state.models import CourseRerunState, CourseRerunUIStateManager
from courseware.courses import get_course_by_id
from custom_settings.models import CustomSettings
from models.settings.course_metadata import CourseMetadata
from xmodule.course_module import CourseFields
from xmodule.modulestore.django import modulestore

from .constants import ERROR_MESSAGES

MODULE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S%z'
RUN_DATE_FORMAT = '%Y%m%d'


def initialize_course_settings(source_course, re_run_course, skip_open_date=True):
    """
    Whenever a new course is created
    1: We add a default entry for the given course in the CustomSettings Model
    2: We add a an honor mode for the given course so students can view certificates
       on their dashboard and progress page
    3: Set rerun course's course open date that exists in the course custom settings
       on the basis of delta from the source_course start date with the source_course course open date
    """

    if not source_course:
        return

    _source_course_settings = CustomSettings.objects.get(id=source_course.id)
    source_course_tags = _source_course_settings.tags
    source_course_is_mini_lesson = _source_course_settings.is_mini_lesson

    source_course_open_date = _source_course_settings.course_open_date

    rerun_course_settings = {
        'tags': source_course_tags,
        'is_mini_lesson': source_course_is_mini_lesson
    }

    if source_course_open_date and not skip_open_date:
        rerun_course_open_date = calculate_date_by_delta(
            source_course_open_date,
            source_course.start,
            re_run_course.start
        )

        rerun_course_settings['course_open_date'] = rerun_course_open_date

    CustomSettings.objects.filter(id=re_run_course.id).update(**rerun_course_settings)


def apply_post_rerun_creation_tasks(source_course_key, destination_course_key, user_id):
    """
    This method is responsible for applying all the tasks after re-run creation has successfully completed

    :param source_course_key: source course key (from which the course was created)
    :param destination_course_key: re run course key (key of the re run created)
    :param user_id: user that created this course
    """
    user = User.objects.get(id=user_id)

    re_run = get_course_by_id(destination_course_key)
    source_course = get_course_by_id(source_course_key)

    # If re run has the default start date, it was created from old flow
    is_default_re_run = re_run.start == CourseFields.start.default

    # initialize course custom settings
    initialize_course_settings(source_course, re_run, is_default_re_run)

    if is_default_re_run:
        return

    # Set course re-run module start and due dates according to the source course
    set_rerun_course_dates(source_course, re_run, user)


def set_rerun_course_dates(source_course, re_run, user):
    """
    This method is responsible for updating all required dates for the re-run course according to
    source course.
    """
    source_course_start_date = source_course.start
    re_run_start_date = re_run.start

    source_course_sections = source_course.get_children()
    source_course_subsections = [sub_section for s in source_course_sections for sub_section in s.get_children()]
    re_run_sections = re_run.get_children()
    re_run_subsections = [sub_section for s in re_run_sections for sub_section in s.get_children()]

    # If there are no sections ignore setting dates
    if not re_run_sections:
        return

    re_run_modules = re_run_sections + re_run_subsections
    source_course_modules = source_course_sections + source_course_subsections

    set_rerun_schedule_dates(re_run, source_course, user)
    set_advanced_settings_due_date(re_run, source_course, user)

    set_rerun_module_dates(re_run_modules, source_course_modules, source_course_start_date, re_run_start_date, user)

    set_rerun_ora_dates(re_run_subsections, re_run_start_date, source_course_start_date, user)


def set_rerun_schedule_dates(re_run_course, source_course, user):
    """
    This methods sets rerun course's enrollment start date, enrollment end date and course end date on the basis
    of delta from the source course's start date
    """
    re_run_course.end = calculate_date_by_delta(source_course.end, source_course.start, re_run_course.start)

    re_run_course.enrollment_start = calculate_date_by_delta(source_course.enrollment_start,
                                                             source_course.start, re_run_course.start)

    re_run_course.enrollment_end = calculate_date_by_delta(source_course.enrollment_end,
                                                           source_course.start, re_run_course.start)

    modulestore().update_item(re_run_course, user.id)


def set_advanced_settings_due_date(re_run_course, source_course, user):
    """
    This methods sets rerun course's due date that exists in the course advanced settings
    on the basis of delta from the source_course start date with the source_course due date

    """
    source_due_date = source_course.due

    if not source_due_date:
        return

    re_run_due_date = calculate_date_by_delta(source_due_date, source_course.start, re_run_course.start)
    CourseMetadata.update_from_dict({'due': re_run_due_date}, re_run_course, user)


def set_rerun_module_dates(re_run_sections, source_course_sections, source_course_start_date, re_run_start_date, user):
    """
    This method is responsible for updating all section and subsection start and due dates for the re-run
    according to source course. This is achieved by calculating the delta between a source section/subsection's
    relevant date and start date, and then adding that delta to the start_date of the re-run course.
    """
    from cms.djangoapps.contentstore.views.item import _save_xblock

    for source_xblock, re_run_xblock in zip(source_course_sections, re_run_sections):
        meta_data = dict()

        meta_data['start'] = calculate_date_by_delta(source_xblock.start, source_course_start_date, re_run_start_date)

        if source_xblock.due:
            meta_data['due'] = calculate_date_by_delta(source_xblock.due, source_course_start_date, re_run_start_date)

        _save_xblock(user, re_run_xblock, metadata=meta_data)


def set_rerun_ora_dates(re_run_subsections, re_run_start_date, source_course_start_date, user):
    """
    This method is responsible for updating all dates in ORA i.e submission, start, due etc, for
    the re-run according to source course. This is achieved by calculating new dates for ORA based
    on delta value.
    :param re_run_subsections: list of subsection in a (re-run) course
    :param re_run_start_date: course start date of source course
    :param source_course_start_date: course start date of source course
    :param user: user that created this course
    """
    def compute_ora_date_by_delta(date_to_update, default_date, date_update_flags):
        """
        Method to calculate new date, on re-run, corresponding to previous value. The delta
        is calculated from course start date of source course and re-run course. Delta is then
        added to previous date in ORA. If date to update is default date then same date is
        returned with negative flag, indicating no need to update date.
        :param date_to_update: submission, start or due date from ORA
        :param default_date: DEFAULT_START or DEFAULT_DUE dates for ORA
        :param date_update_flags: list containing flags, indicating corresponding date changes or not
        :return: date string and boolean flag indicating need for updating ORA date
        """
        date_update_required = date_to_update and not date_to_update.startswith(default_date)
        updated_date = date_to_update

        if date_update_required:
            updated_date = calculate_date_by_delta(parse(date_to_update), source_course_start_date,
                                                   re_run_start_date)
            updated_date = updated_date.strftime(MODULE_DATE_FORMAT)

        date_update_flags.append(date_update_required)
        return updated_date

    # flat sub-sections to the level of components and pick ORA only
    re_run_ora_list = [
        component
        for subsection in re_run_subsections
        for unit in subsection.get_children()
        for component in unit.get_children()
        if component.category == 'openassessment'
    ]

    for ora in re_run_ora_list:
        date_update_flags = list()
        ora.submission_start = compute_ora_date_by_delta(ora.submission_start, DEFAULT_START, date_update_flags)
        ora.submission_due = compute_ora_date_by_delta(ora.submission_due, DEFAULT_DUE, date_update_flags)

        for assessment in ora.rubric_assessments:
            if 'start' in assessment:
                assessment['start'] = compute_ora_date_by_delta(assessment['start'], DEFAULT_START, date_update_flags)
            if 'due' in assessment:
                assessment['due'] = compute_ora_date_by_delta(assessment['due'], DEFAULT_DUE, date_update_flags)

        # If all dates in ORA are default then no need to update it during re-run process
        if not any(date_update_flags):
            continue

        component_update(ora, user)


def component_update(descriptor, user):
    """
    This method is responsible for updating provided component i.e. peer assessment
    :param descriptor: component to update
    :param user: user that is updating component
    """
    from cms.djangoapps.contentstore.views.item import StudioEditModuleRuntime

    descriptor.xmodule_runtime = StudioEditModuleRuntime(user)
    modulestore().update_item(descriptor, user.id)


def calculate_date_by_delta(date, source_date, destination_date):
    """
    This method is used to compute a date with a delta based on the difference of source_date and date
    and adding that delta to the destination date
    :param date: date for which delta is to be calculated
    :param source_date: date from which delta is to be calculated
    :param destination_date: date into which delta is to be added
    """

    # Sometimes date is coming without timezone (primarily in case of ORA)
    # Hence we'll be adding default timezone i.e. UTC to the datetime object passed
    if not date.tzinfo:
        date = date.replace(tzinfo=utc)

    date_delta = source_date - date
    return destination_date - date_delta


def update_course_re_run_details(course_re_run_details):
    """
    This method gets new rerun data in dict and return it with necessary data for rerun creation
    along with updated run id's for each rerun
    :param course_re_run_details: dict containing rerun data for all courses
    :return: the input dictionary updated with a generated run id for all reruns and all fields
             necessary for re-run creation
    """
    for course_detail in course_re_run_details:
        course_key = CourseKey.from_string(course_detail['source_course_key'])

        # replacing string course key with course key object in course rerun details dict
        course_detail['source_course_key'] = course_key
        source_course = modulestore().get_course(course_key)

        error_messages = []

        if not source_course.end:
            error_messages.append(ERROR_MESSAGES['course_end_date_missing'])

        if not source_course.enrollment_start:
            error_messages.append(ERROR_MESSAGES['enrollment_start_date_missing'])

        if not source_course.enrollment_end:
            error_messages.append(ERROR_MESSAGES['enrollment_end_date_missing'])

        if error_messages:
            raise_rerun_creation_exception(course_detail, ' '.join(error_messages), exception_class=Exception)

        run_number = calculate_next_rerun_number(source_course.id)

        course_detail['display_name'] = source_course.display_name
        course_detail['number'] = source_course.number
        course_detail['org'] = source_course.org

        runs = course_detail['runs']

        for re_run_index, run in enumerate(runs):
            # create new rerun id and increment each rerun number
            run['run'] = create_new_run_id(run, source_course, run_number + re_run_index)

    return course_re_run_details


def calculate_next_rerun_number(source_course_id):
    """
    This method will calculate next rerun number, which should be used for creating course rerun
    :param source_course_id: Id of the source_course
    :return: new run number
    """
    split_course_run = source_course_id.run.split('_')

    # validate rerun number, valid run number must have four sections
    if len(split_course_run) == 4 and split_course_run[0].isdigit():
        # if run number pass basic validation then extract run number and increment it
        return int(split_course_run[0]) + 1
    else:
        # If run number can not be extracted from run number than
        # count all rerun in group and use it as run number
        return len(get_course_group(source_course_id)) + 1


def create_new_run_id(run_dict, course, run_number):
    """
    This method will create complete new run id for rerun course
    :param run_dict: dict containing run details provided by user
    :param course: Source course of which rerun is being created
    :param run_number: new calculated run number
    :return: complete new run id
    """
    if not run_dict.get('release_number'):
        raise_rerun_creation_exception(run_dict, ERROR_MESSAGES['release_number_missing'], exception_class=Exception)


    course_end_date = calculate_date_by_delta(run_dict['start'], course.start, course.end)

    new_run_id = "{}_{}_{}_{}".format(
        run_number, run_dict['release_number'], run_dict['start'].strftime(RUN_DATE_FORMAT),
        course_end_date.strftime(RUN_DATE_FORMAT)
    )
    return new_run_id


def get_course_group(course_key):
    """
    This method evaluates a course's family(all related courses) to which it belongs to.

    A course can be of 3 types:

    - Course Rerun - method will return all its sibling re runs along with its parent
                     sorted by order creation time(latest first)
    - Parent Course - method will return all its child re runs along with its parent
                      sorted by order creation time(latest first)
    - Course Without Rerun - will return only the course itself

    """
    course_rerun = CourseRerunState.objects.filter(course_key=course_key).first()
    is_course_parent_course = not bool(course_rerun) and bool(CourseRerunState.objects.filter(
        source_course_key=course_key,
        state=CourseRerunUIStateManager.State.SUCCEEDED)
    )

    if not course_rerun and not is_course_parent_course:
        return [course_key]

    parent_course_key = course_key

    # Relevant course key for a course which is a rerun would be its parent's course key
    if not is_course_parent_course:
        parent_course_key = course_rerun.source_course_key

    courses = [
        c.course_key
        for c in
        CourseRerunState.objects.filter(
            source_course_key=parent_course_key,
            state=CourseRerunUIStateManager.State.SUCCEEDED).order_by(
            '-created_time').all()
    ]
    courses.append(parent_course_key)

    return courses


def raise_rerun_creation_exception(details_dict, error_message, exception_class=None):
    """
    This method adds an error message in the details_dict

    :param details_dict: either a dictionary of a re-run or a course.
    :param error_message: error message to set
    :param exception_class: the exception class to raise

    :return: if an exception_class is passed, this method raises that exception
             otherwise returns error_message
    """
    details_dict['error'] = error_message

    if exception_class:
        raise exception_class(error_message)

    return error_message


def latest_course_reruns(courses):
    """
    This method evaluates only the latest reruns of all given courses
    :param courses: list of courses to compute latest courses from
    :return: list of latest course reruns (CourseSummary Objects)
    """
    courses_map = {course.id: course for course in courses}
    latest_courses = list()
    visited_courses = set()

    for course in courses:
        if course.id in visited_courses:
            continue

        course_group = get_course_group(course.id)

        # Adding this course's group to set of visited courses
        visited_courses |= set(course_group)

        latest_course_id = course_group[0]

        # Adding latest course id to list of latest course ids
        if latest_course_id in courses_map:
            latest_courses.append(courses_map[latest_course_id])

    return latest_courses
