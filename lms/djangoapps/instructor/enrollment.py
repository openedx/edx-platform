"""
Enrollment operations for use by instructor APIs.

Does not include any access control, be sure to check access before calling.
"""

import re
import json
from django.contrib.auth.models import User
from student.models import CourseEnrollment, CourseEnrollmentAllowed
from courseware.models import StudentModule


def enroll_emails(course_id, student_emails, auto_enroll=False):
    """
    Enroll multiple students by email.

    students is a list of student emails e.g. ["foo@bar.com", "bar@foo.com]
    each of whom possibly does not exist in db.

    status contains the relevant prior state and action performed on the user.
    ce stands for CourseEnrollment
    cea stands for CourseEnrollmentAllowed
    ! stands for the object not existing prior to the action
    return a mapping from status to emails.
    """

    auto_string = {False: 'allowed', True: 'willautoenroll'}[auto_enroll]

    status_map = {
        'user/ce/alreadyenrolled':   [],
        'user/!ce/enrolled':         [],
        'user/!ce/rejected':         [],
        '!user/cea/' + auto_string:  [],
        '!user/!cea/' + auto_string: [],
    }

    for student_email in student_emails:
        # status: user
        try:
            user = User.objects.get(email=student_email)

            # status: user/ce
            try:
                CourseEnrollment.objects.get(user=user, course_id=course_id)
                status_map['user/ce/alreadyenrolled'].append(student_email)
            # status: user/!ce
            except CourseEnrollment.DoesNotExist:
                # status: user/!ce/enrolled
                try:
                    ce = CourseEnrollment(user=user, course_id=course_id)
                    ce.save()
                    status_map['user/!ce/enrolled'].append(student_email)
                # status: user/!ce/rejected
                except:
                    status_map['user/!ce/rejected'].append(student_email)
        # status: !user
        except User.DoesNotExist:
            # status: !user/cea
            try:
                cea = CourseEnrollmentAllowed.objects.get(course_id=course_id, email=student_email)
                cea.auto_enroll = auto_enroll
                cea.save()
                status_map['!user/cea/' + auto_string].append(student_email)
            # status: !user/!cea
            except CourseEnrollmentAllowed.DoesNotExist:
                cea = CourseEnrollmentAllowed(course_id=course_id, email=student_email, auto_enroll=auto_enroll)
                cea.save()
                status_map['!user/!cea/' + auto_string].append(student_email)

    return status_map


def unenroll_emails(course_id, student_emails):
    """
    Unenroll multiple students by email.

    students is a list of student emails e.g. ["foo@bar.com", "bar@foo.com]
    each of whom possibly does not exist in db.

    Fail quietly on student emails that do not match any users or allowed enrollments.

    status contains the relevant prior state and action performed on the user.
    ce stands for CourseEnrollment
    cea stands for CourseEnrollmentAllowed
    ! stands for the object not existing prior to the action
    return a mapping from status to emails.
    """

    # NOTE these are not mutually exclusive
    status_map = {
        'cea/disallowed': [],
        'ce/unenrolled': [],
        'ce/rejected': [],
        '!ce/notenrolled': [],
    }

    for student_email in student_emails:
        # delete CourseEnrollmentAllowed
        try:
            cea = CourseEnrollmentAllowed.objects.get(course_id=course_id, email=student_email)
            cea.delete()
            status_map['cea/disallowed'].append(student_email)
        except CourseEnrollmentAllowed.DoesNotExist:
            pass

        # delete CourseEnrollment
        try:
            ce = CourseEnrollment.objects.get(course_id=course_id, user__email=student_email)
            try:
                ce.delete()
                status_map['ce/unenrolled'].append(student_email)
            except Exception:
                status_map['ce/rejected'].append(student_email)
        except CourseEnrollment.DoesNotExist:
            status_map['!ce/notenrolled'].append(student_email)

    return status_map


def split_input_list(str_list):
    """
    Separate out individual student email from the comma, or space separated string.

    e.g.
    in: "Lorem@ipsum.dolor, sit@amet.consectetur\nadipiscing@elit.Aenean\r convallis@at.lacus\r, ut@lacinia.Sed"
    out: ['Lorem@ipsum.dolor', 'sit@amet.consectetur', 'adipiscing@elit.Aenean', 'convallis@at.lacus', 'ut@lacinia.Sed']

    In:
    students: string coming from the input text area
    Return:
    students: list of cleaned student emails
    students_lc: list of lower case cleaned student emails
    """

    new_list = re.split(r'[\n\r\s,]', str_list)
    new_list = [str(s.strip()) for s in new_list]
    new_list = [s for s in new_list if s != '']

    return new_list


def reset_student_attempts(course_id, student, problem_to_reset, delete_module=False):
    """
    Reset student attempts for a problem. Optionally deletes all student state for the specified problem.

    In the previous instructor dashboard it was possible to modify/delete
    modules that were not problems. That has been disabled for safety.

    student is a User
    problem_to_reset is the name of a problem e.g. 'L2Node1'.
    To build the module_state_key 'problem/' and course information will be appended to problem_to_reset.
    """
    if problem_to_reset[-4:] == ".xml":
        problem_to_reset = problem_to_reset[:-4]

    problem_to_reset = "problem/" + problem_to_reset

    (org, course_name, _) = course_id.split("/")
    module_state_key = "i4x://" + org + "/" + course_name + "/" + problem_to_reset
    module_to_reset = StudentModule.objects.get(student_id=student.id,
                                                course_id=course_id,
                                                module_state_key=module_state_key)

    if delete_module:
        module_to_reset.delete()
    else:
        _reset_module_attempts(module_to_reset)


def _reset_module_attempts(studentmodule):
    """ Reset the number of attempts on a studentmodule. """
    # load the state json
    problem_state = json.loads(studentmodule.state)
    # old_number_of_attempts = problem_state["attempts"]
    problem_state["attempts"] = 0

    # save
    studentmodule.state = json.dumps(problem_state)
    studentmodule.save()
    # track.views.server_track(request,
    #                          '{instructor} reset attempts from {old_attempts} to 0 for {student} on problem {problem} in {course}'.format(
    #                              old_attempts=old_number_of_attempts,
    #                              student=student_to_reset,
    #                              problem=studentmodule.module_state_key,
    #                              instructor=request.user,
    #                              course=course_id),
    #                          {},
    #                          page='idashboard')
