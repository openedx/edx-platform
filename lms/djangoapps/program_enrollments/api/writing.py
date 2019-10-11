"""
Python API functions related to writing program enrollments.

Outside of this subpackage, import these functions
from `lms.djangoapps.program_enrollments.api`.
"""
from __future__ import absolute_import, unicode_literals

import logging

from course_modes.models import CourseMode
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment, NonExistentCourseError

from ..constants import ProgramCourseEnrollmentStatuses
from ..constants import ProgramCourseOperationStatuses as ProgramCourseOpStatuses
from ..constants import ProgramEnrollmentStatuses
from ..constants import ProgramOperationStatuses as ProgramOpStatuses
from ..exceptions import ProviderDoesNotExistException
from ..models import ProgramCourseEnrollment, ProgramEnrollment
from .reading import fetch_program_course_enrollments, fetch_program_enrollments, get_users_by_external_keys

logger = logging.getLogger(__name__)


def write_program_enrollments(program_uuid, enrollment_requests, create, update):
    """
    Bulk create/update a set of program enrollments.

    Arguments:
        program_uuid (UUID|str)
        enrollment_requests (list[dict]): dicts in the form:
            * 'external_user_key': str
            * 'status': str from ProgramEnrollmentStatuses
            * 'curriculum_uuid': str, omittable if `create==False`.
        create (bool): non-existent enrollments will be created iff `create`,
            otherwise they will be skipped as 'duplicate'.
        update (bool): existing enrollments will be updated iff `update`,
            otherwise they will be skipped as 'not-in-program'

    At least one of `create` or `update` must be True.

    Returns: dict[str: str]
        Mapping of external user keys to strings from ProgramOperationStatuses.
    """
    if not (create or update):
        raise ValueError("At least one of (create, update) must be True")
    requests_by_key, duplicated_keys = _organize_requests_by_external_key(enrollment_requests)
    external_keys = set(requests_by_key)
    try:
        users_by_key = get_users_by_external_keys(program_uuid, external_keys)
    except ProviderDoesNotExistException:
        # Organization has not yet set up their identity provider.
        # Just act as if none of the external users have been registered.
        users_by_key = {key: None for key in external_keys}

    # Fetch existing program enrollments.
    existing_enrollments = fetch_program_enrollments(
        program_uuid=program_uuid, external_user_keys=external_keys
    )
    existing_enrollments_by_key = {key: None for key in external_keys}
    existing_enrollments_by_key.update({
        enrollment.external_user_key: enrollment
        for enrollment in existing_enrollments
    })

    # For each enrollment request, try to create/update:
    # * For creates, build up list `to_save`, which we will bulk-create afterwards.
    # * For updates, do them in place.
    #     (TODO: Django 2.2 will add bulk-update support, which we could use here)
    # Update `results` with the new status or an error status for each operation.
    results = {}
    to_save = []
    for external_key, request in requests_by_key.items():
        status = request['status']
        if status not in ProgramEnrollmentStatuses.__ALL__:
            results[external_key] = ProgramOpStatuses.INVALID_STATUS
            continue
        user = users_by_key[external_key]
        existing_enrollment = existing_enrollments_by_key.get(external_key)
        if existing_enrollment:
            if not update:
                results[external_key] = ProgramOpStatuses.CONFLICT
                continue
            results[external_key] = change_program_enrollment_status(
                existing_enrollment, status
            )
        else:
            if not create:
                results[external_key] = ProgramOpStatuses.NOT_IN_PROGRAM
                continue
            new_enrollment = create_program_enrollment(
                program_uuid=program_uuid,
                curriculum_uuid=request['curriculum_uuid'],
                user=user,
                external_user_key=external_key,
                status=status,
                save=False,
            )
            to_save.append(new_enrollment)
            results[external_key] = new_enrollment.status

    # Bulk-create all new program enrollments.
    # Note: this will NOT invoke `save()` or `pre_save`/`post_save` signals!
    # See https://docs.djangoproject.com/en/1.11/ref/models/querysets/#bulk-create.
    if to_save:
        ProgramEnrollment.objects.bulk_create(to_save)

    results.update({key: ProgramOpStatuses.DUPLICATED for key in duplicated_keys})
    return results


def create_program_enrollment(
        program_uuid,
        curriculum_uuid,
        user,
        external_user_key,
        status,
        save=True,
):
    """
    Create a program enrollment.

    Arguments:
        program_uuid (UUID|str)
        curriculum_uuid (str)
        user (User)
        external_user_key (str)
        status (str): from ProgramEnrollmentStatuses
        save (bool): Whether to save the created ProgamEnrollment.
            Defaults to True. One may set this to False in order to
            bulk-create the enrollments.

    Returns: ProgramEnrollment
    """
    if not (user or external_user_key):
        raise ValueError("At least one of (user, external_user_key) must be ")
    program_enrollment = ProgramEnrollment(
        program_uuid=program_uuid,
        curriculum_uuid=curriculum_uuid,
        user=user,
        external_user_key=external_user_key,
        status=status,
    )
    if save:
        program_enrollment.save()
    return program_enrollment


def change_program_enrollment_status(program_enrollment, new_status):
    """
    Update a program enrollment with a new status.

    Arguments:
        program_enrollment (ProgramEnrollment)
        status (str): from ProgramCourseEnrollmentStatuses

    Returns: str
        String from ProgramOperationStatuses.
    """
    if new_status not in ProgramEnrollmentStatuses.__ALL__:
        return ProgramOpStatuses.INVALID_STATUS
    program_enrollment.status = new_status
    program_enrollment.save()
    return program_enrollment.status


def write_program_course_enrollments(
        program_uuid,
        course_key,
        enrollment_requests,
        create,
        update,
):
    """
    Bulk create/update a set of program-course enrollments.

    Arguments:
        program_uuid (UUID|str)
        enrollment_requests (list[dict]): dicts in the form:
            * 'external_user_key': str
            * 'status': str from ProgramCourseEnrollmentStatuses
        create (bool): non-existent enrollments will be created iff `create`,
            otherwise they will be skipped as 'duplicate'.
        update (bool): existing enrollments will be updated iff `update`,
            otherwise they will be skipped as 'not-in-program'

    At least one of `create` or `update` must be True.

    Returns: dict[str: str]
        Mapping of external user keys to strings from ProgramCourseOperationStatuses.
    """
    if not (create or update):
        raise ValueError("At least one of (create, update) must be True")
    requests_by_key, duplicated_keys = _organize_requests_by_external_key(enrollment_requests)
    external_keys = set(requests_by_key)
    program_enrollments = fetch_program_enrollments(
        program_uuid=program_uuid,
        external_user_keys=external_keys,
    ).prefetch_related('program_course_enrollments')
    program_enrollments_by_key = {
        enrollment.external_user_key: enrollment for enrollment in program_enrollments
    }

    # Fetch existing program-course enrollments.
    existing_course_enrollments = fetch_program_course_enrollments(
        program_uuid, course_key, program_enrollments=program_enrollments,
    )
    existing_course_enrollments_by_key = {key: None for key in external_keys}
    existing_course_enrollments_by_key.update({
        enrollment.program_enrollment.external_user_key: enrollment
        for enrollment in existing_course_enrollments
    })

    # For each enrollment request, try to create/update.
    # For creates, build up list `to_save`, which we will bulk-create afterwards.
    # For updates, do them in place (Django 2.2 will add bulk-update support).
    # For each operation, update `results` with the new status or an error status.
    results = {}
    to_save = []
    for external_key, request in requests_by_key.items():
        status = request['status']
        if status not in ProgramCourseEnrollmentStatuses.__ALL__:
            results[external_key] = ProgramCourseOpStatuses.INVALID_STATUS
            continue
        program_enrollment = program_enrollments_by_key.get(external_key)
        if not program_enrollment:
            results[external_key] = ProgramCourseOpStatuses.NOT_IN_PROGRAM
            continue
        existing_course_enrollment = existing_course_enrollments_by_key[external_key]
        if existing_course_enrollment:
            if not update:
                results[external_key] = ProgramCourseOpStatuses.CONFLICT
                continue
            results[external_key] = change_program_course_enrollment_status(
                existing_course_enrollment, status
            )
        else:
            if not create:
                results[external_key] = ProgramCourseOpStatuses.NOT_FOUND
                continue
            new_course_enrollment = create_program_course_enrollment(
                program_enrollment, course_key, status, save=False
            )
            to_save.append(new_course_enrollment)
            results[external_key] = new_course_enrollment.status

    # Bulk-create all new program-course enrollments.
    # Note: this will NOT invoke `save()` or `pre_save`/`post_save` signals!
    # See https://docs.djangoproject.com/en/1.11/ref/models/querysets/#bulk-create.
    if to_save:
        ProgramCourseEnrollment.objects.bulk_create(to_save)

    results.update({
        key: ProgramCourseOpStatuses.DUPLICATED for key in duplicated_keys
    })
    return results


def create_program_course_enrollment(program_enrollment, course_key, status, save=True):
    """
    Create a program course enrollment.

    If `program_enrollment` is realized (i.e., has a non-null User),
    then also create a course enrollment.

    Arguments:
        program_enrollment (ProgramEnrollment)
        course_key (CourseKey|str)
        status (str): from ProgramCourseEnrollmentStatuses
        save (bool): Whether to save the created ProgamCourseEnrollment.
            Defaults to True. One may set this to False in order to
            bulk-create the enrollments.
            Note that if a CourseEnrollment is created, it will be saved
            regardless of this value.

    Returns: ProgramCourseEnrollment

    Raises: NonExistentCourseError
    """
    _ensure_course_exists(course_key, program_enrollment.external_user_key)
    course_enrollment = (
        enroll_in_masters_track(program_enrollment.user, course_key, status)
        if program_enrollment.user
        else None
    )
    program_course_enrollment = ProgramCourseEnrollment(
        program_enrollment=program_enrollment,
        course_key=course_key,
        course_enrollment=course_enrollment,
        status=status,
    )
    if save:
        program_course_enrollment.save()
    return program_course_enrollment


def change_program_course_enrollment_status(program_course_enrollment, new_status):
    """
    Update a program course enrollment with a new status.

    If `program_course_enrollment` is realized with a CourseEnrollment,
    then also update that.

    Arguments:
        program_course_enrollment (ProgramCourseEnrollment)
        status (str): from ProgramCourseEnrollmentStatuses

    Returns: str
        String from ProgramOperationCourseStatuses.
    """
    if new_status == program_course_enrollment.status:
        return new_status
    if new_status == ProgramCourseEnrollmentStatuses.ACTIVE:
        active = True
    elif new_status == ProgramCourseEnrollmentStatuses.INACTIVE:
        active = False
    else:
        return ProgramCourseOpStatuses.INVALID_STATUS
    if program_course_enrollment.course_enrollment:
        if active:
            program_course_enrollment.course_enrollment.activate()
        else:
            program_course_enrollment.course_enrollment.deactivate()
    program_course_enrollment.status = new_status
    program_course_enrollment.save()
    return program_course_enrollment.status


def enroll_in_masters_track(user, course_key, status):
    """
    Ensure that the user is enrolled in the Master's track of course.
    Either creates or updates a course enrollment.

    Arguments:
        user (User)
        course_key (CourseKey|str)
        status (str): from ProgramCourseEnrollmenStatuses

    Returns: CourseEnrollment

    Raises: NonExistentCourseError
    """
    _ensure_course_exists(course_key, user.id)
    if status not in ProgramCourseEnrollmentStatuses.__ALL__:
        raise ValueError("invalid ProgramCourseEnrollmenStatus: {}".format(status))
    if CourseEnrollment.is_enrolled(user, course_key):
        course_enrollment = CourseEnrollment.objects.get(
            user=user,
            course_id=course_key,
        )
        if course_enrollment.mode in {CourseMode.AUDIT, CourseMode.HONOR}:
            course_enrollment.mode = CourseMode.MASTERS
            course_enrollment.save()
            message_template = (
                "Converted course enrollment for user id={} "
                "and course key={} from mode {} to Master's."
            )
            logger.info(
                message_template.format(user.id, course_key, course_enrollment.mode)
            )
        elif course_enrollment.mode != CourseMode.MASTERS:
            error_message = (
                "Cannot convert CourseEnrollment to Master's from mode {}. "
                "user id={}, course_key={}."
            ).format(
                course_enrollment.mode, user.id, course_key
            )
            logger.error(error_message)
    else:
        course_enrollment = CourseEnrollment.enroll(
            user,
            course_key,
            mode=CourseMode.MASTERS,
            check_access=False,
        )
    if course_enrollment.mode == CourseMode.MASTERS:
        if status == ProgramCourseEnrollmentStatuses.INACTIVE:
            course_enrollment.deactivate()
    return course_enrollment


def _ensure_course_exists(course_key, user_key_or_id):
    """
    Log and raise an error if `course_key` does not refer to a real course run.

    `user_key_or_id` should be a non-PII value identifying the user that
    can be used in the log message.
    """
    if CourseOverview.course_exists(course_key):
        return
    logger.error(
        "Cannot enroll user={} in non-existent course={}".format(
            user_key_or_id,
            course_key,
        )
    )
    raise NonExistentCourseError


def _organize_requests_by_external_key(enrollment_requests):
    """
    Get dict of enrollment requests by external key.
    External keys associated with more than one request are split out into a set,
        and their enrollment requests thrown away.

    Arguments:
        enrollment_requests (list[dict])

    Returns:
        (requests_by_key, duplicated_keys)
        where requests_by_key is dict[str: dict]
          and duplicated_keys is set[str].
    """
    requests_by_key = {}
    duplicated_keys = set()
    for request in enrollment_requests:
        key = request['external_user_key']
        if key in duplicated_keys:
            continue
        if key in requests_by_key:
            duplicated_keys.add(key)
            del requests_by_key[key]
            continue
        requests_by_key[key] = request
    return requests_by_key, duplicated_keys
