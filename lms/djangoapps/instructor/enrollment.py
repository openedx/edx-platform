"""
Enrollment operations for use by instructor APIs.

Does not include any access control, be sure to check access before calling.
"""

import json
from django.contrib.auth.models import User
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from courseware.models import StudentModule


class EmailEnrollmentState(object):
    """ Store the complete enrollment state of an email in a class """
    def __init__(self, course_id, email):
        exists_user = User.objects.filter(email=email).exists()
        exists_ce = CourseEnrollment.objects.filter(course_id=course_id, user__email=email).exists()
        ceas = CourseEnrollmentAllowed.objects.filter(course_id=course_id, email=email).all()
        exists_allowed = len(ceas) > 0
        state_auto_enroll = exists_allowed and ceas[0].auto_enroll

        self.user = exists_user
        self.enrollment = exists_ce
        self.allowed = exists_allowed
        self.auto_enroll = bool(state_auto_enroll)

    def __repr__(self):
        return "{}(user={}, enrollment={}, allowed={}, auto_enroll={})".format(
            self.__class__.__name__,
            self.user,
            self.enrollment,
            self.allowed,
            self.auto_enroll,
        )

    def to_dict(self):
        """
        example: {
            'user': False,
            'enrollment': False,
            'allowed': True,
            'auto_enroll': True,
        }
        """
        return {
            'user': self.user,
            'enrollment': self.enrollment,
            'allowed': self.allowed,
            'auto_enroll': self.auto_enroll,
        }


def enroll_email(course_id, student_email, auto_enroll=False):
    """
    Enroll a student by email.

    `student_email` is student's emails e.g. "foo@bar.com"
    `auto_enroll` determines what is put in CourseEnrollmentAllowed.auto_enroll
        if auto_enroll is set, then when the email registers, they will be
        enrolled in the course automatically.

    returns two EmailEnrollmentState's
        representing state before and after the action.
    """

    previous_state = EmailEnrollmentState(course_id, student_email)

    if previous_state.user:
        user = User.objects.get(email=student_email)
        CourseEnrollment.objects.get_or_create(course_id=course_id, user=user)
    else:
        cea, _ = CourseEnrollmentAllowed.objects.get_or_create(course_id=course_id, email=student_email)
        cea.auto_enroll = auto_enroll
        cea.save()

    after_state = EmailEnrollmentState(course_id, student_email)

    return previous_state, after_state


def unenroll_email(course_id, student_email):
    """
    Unenroll a student by email.

    `student_email` is student's emails e.g. "foo@bar.com"

    returns two EmailEnrollmentState's
        representing state before and after the action.
    """

    previous_state = EmailEnrollmentState(course_id, student_email)

    if previous_state.enrollment:
        CourseEnrollment.objects.get(course_id=course_id, user__email=student_email).delete()

    if previous_state.allowed:
        CourseEnrollmentAllowed.objects.get(course_id=course_id, email=student_email).delete()

    after_state = EmailEnrollmentState(course_id, student_email)

    return previous_state, after_state


def reset_student_attempts(course_id, student, module_state_key, delete_module=False):
    """
    Reset student attempts for a problem. Optionally deletes all student state for the specified problem.

    In the previous instructor dashboard it was possible to modify/delete
    modules that were not problems. That has been disabled for safety.

    `student` is a User
    `problem_to_reset` is the name of a problem e.g. 'L2Node1'.
    To build the module_state_key 'problem/' and course information will be appended to `problem_to_reset`.

    Throws ValueError if `problem_state` is invalid JSON.
    """
    module_to_reset = StudentModule.objects.get(student_id=student.id,
                                                course_id=course_id,
                                                module_state_key=module_state_key)

    if delete_module:
        module_to_reset.delete()
    else:
        _reset_module_attempts(module_to_reset)


def _reset_module_attempts(studentmodule):
    """
    Reset the number of attempts on a studentmodule.

    Throws ValueError if `problem_state` is invalid JSON.
    """
    # load the state json
    problem_state = json.loads(studentmodule.state)
    # old_number_of_attempts = problem_state["attempts"]
    problem_state["attempts"] = 0

    # save
    studentmodule.state = json.dumps(problem_state)
    studentmodule.save()
