"""
Enrollment API for creating, updating, and deleting enrollments. Also provides access to enrollment information at a
course level, such as available course modes.

"""
from enrollment import data


class CourseEnrollmentError(Exception):
    """ Generic Course Enrollment Error.

    Describes any error that may occur when reading or updating enrollment information for a student or a course.

    """
    pass


def get_enrollments(student_id):
    """ Retrieves all the courses a student is enrolled in.

    Takes a student and retrieves all relative enrollments. Includes information regarding how the student is enrolled
    in the the course.

    Args:
        student_id (str): The ID of the student we want to retrieve course enrollment information for.

    Returns:
        A list of enrollment information for the given student.

    Examples:
        >>> get_enrollments("Bob")
        [
            {
                course_id: "edX/DemoX/2014T2",
                is_active: True,
                mode: "honor",
                student: "Bob",
                course_modes: [
                    "audit",
                    "honor"
                ],
                enrollment_start: 2014-04-07,
                enrollment_end: 2014-06-07,
                invite_only: False
            },
            {
                course_id: "edX/edX-Insider/2014T2",
                is_active: True,
                mode: "honor",
                student: "Bob",
                course_modes: [
                    "audit",
                    "honor",
                    "verified"
                ],
                enrollment_start: 2014-05-01,
                enrollment_end: 2014-06-01,
                invite_only: True
            },
        ]

    """
    return data.get_course_enrollments(student_id)


def get_enrollment(student_id, course_id):
    """ Retrieves all enrollment information for the student in respect to a specific course.

    Gets all the course enrollment information specific to a student in a course.

    Args:
        student_id (str): The student to get course enrollment information for.
        course_id (str): The course to get enrollment information for.

    Returns:
        A serializable dictionary of the course enrollment.

    Example:
        >>> add_enrollment("Bob", "edX/DemoX/2014T2")
        {
            course_id: "edX/DemoX/2014T2",
            is_active: True,
            mode: "honor",
            student: "Bob",
            course_modes: [
                "audit",
                "honor"
            ],
            enrollment_start: 2014-04-07,
            enrollment_end: 2014-06-07,
            invite_only: False
        }

    """
    return data.get_course_enrollment(student_id, course_id)


def add_enrollment(student_id, course_id, mode='honor', is_active=True):
    """ Enrolls a student in a course.

    Enrolls a student in a course. If the mode is not specified, this will default to 'honor'.

    Args:
        student_id (str): The student to enroll.
        course_id (str): The course to enroll the student in.
        mode (str): Optional argument for the type of enrollment to create. Ex. 'audit', 'honor', 'verified',
            'professional'. If not specified, this defaults to 'honor'.
        is_active (boolean): Optional argument for making the new enrollment inactive. If not specified, is_active
            defaults to True.

    Returns:
        A serializable dictionary of the new course enrollment.

    Example:
        >>> add_enrollment("Bob", "edX/DemoX/2014T2", mode="audit")
        {
            course_id: "edX/DemoX/2014T2",
            is_active: True,
            mode: "audit",
            student: "Bob",
            course_modes: [
                "audit",
                "honor"
            ],
            enrollment_start: 2014-04-07,
            enrollment_end: 2014-06-07,
            invite_only: False
        }
    """
    return data.update_course_enrollment(student_id, course_id, mode=mode, is_active=is_active)


def deactivate_enrollment(student_id, course_id):
    """ Un-enrolls a student in a course

    Deactivate the enrollment of a student in a course. We will not remove the enrollment data, but simply flag it
    as inactive.

    Args:
        student_id (str): The student associated with the deactivated enrollment.
        course_id (str): The course associated with the deactivated enrollment.

    Returns:
        A serializable dictionary representing the deactivated course enrollment for the student.

    Example:
        >>> deactivate_enrollment("Bob", "edX/DemoX/2014T2")
        {
            course_id: "edX/DemoX/2014T2",
            mode: "honor",
            is_active: False,
            student: "Bob",
            course_modes: [
                "audit",
                "honor"
            ],
            enrollment_start: 2014-04-07,
            enrollment_end: 2014-06-07,
            invite_only: False
        }
    """
    return data.update_course_enrollment(student_id, course_id, is_active=False)


def update_enrollment(student_id, course_id, mode):
    """ Updates the course mode for the enrolled user.

    Update a course enrollment for the given student and course.

    Args:
        student_id (str): The student associated with the updated enrollment.
        course_id (str): The course associated with the updated enrollment.
        mode (str): The new course mode for this enrollment.

    Returns:
        A serializable dictionary representing the updated enrollment.

    Example:
        >>> update_enrollment("Bob", "edX/DemoX/2014T2", "honor")
        {
            course_id: "edX/DemoX/2014T2",
            mode: "honor",
            is_active: True,
            student: "Bob",
            course_modes: [
                "audit",
                "honor"
            ],
            enrollment_start: 2014-04-07,
            enrollment_end: 2014-06-07,
            invite_only: False
        }

    """
    return data.update_course_enrollment(student_id, course_id, mode)


def get_course_enrollment_details(course_id):
    """ Get the course modes for course. Also get enrollment start and end date, invite only, etc.

    Given a course_id, return a serializable dictionary of properties describing course enrollment information.

    Args:
        course_id (str): The Course to get enrollment information for.

    Returns:
        A serializable dictionary of course enrollment information.

    Example:
        >>> get_course_enrollment_details("edX/DemoX/2014T2")
        {
            course_id: "edX/DemoX/2014T2",
            course_modes: [
                "audit",
                "honor"
            ],
            enrollment_start: 2014-04-01,
            enrollment_end: 2014-06-01,
            invite_only: False
        }

    """
    pass
