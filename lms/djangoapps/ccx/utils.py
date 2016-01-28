"""
CCX Enrollment operations for use by Coach APIs.

Does not include any access control, be sure to check access before calling.
"""
import datetime
import logging
import pytz
from contextlib import contextmanager

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.core.validators import validate_email

from courseware.courses import get_course_by_id
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor
from instructor.enrollment import (
    enroll_email,
    unenroll_email,
)
from instructor.access import allow_access
from instructor.views.tools import get_student_from_identifier
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment
from student.roles import CourseCcxCoachRole

from lms.djangoapps.ccx.models import CustomCourseForEdX
from lms.djangoapps.ccx.overrides import get_override_for_ccx
from lms.djangoapps.ccx.custom_exception import CCXUserValidationException

log = logging.getLogger("edx.ccx")


def get_ccx_from_ccx_locator(course_id):
    """ helper function to allow querying ccx fields from templates """
    ccx_id = getattr(course_id, 'ccx', None)
    ccx = None
    if ccx_id:
        ccx = CustomCourseForEdX.objects.filter(id=ccx_id)
    if not ccx:
        log.warning(
            "CCX does not exist for course with id %s",
            course_id
        )
        return None
    return ccx[0]


def get_date(ccx, node, date_type=None, parent_node=None):
    """
    This returns override or master date for section, subsection or a unit.

    :param ccx: ccx instance
    :param node: chapter, subsection or unit
    :param date_type: start or due
    :param parent_node: parent of node
    :return: start or due date
    """
    date = get_override_for_ccx(ccx, node, date_type, None)
    if date_type == "start":
        master_date = node.start
    else:
        master_date = node.due

    if date is not None:
        # Setting override date [start or due]
        date = date.strftime('%Y-%m-%d %H:%M')
    elif not parent_node and master_date is not None:
        # Setting date from master course
        date = master_date.strftime('%Y-%m-%d %H:%M')
    elif parent_node is not None:
        # Set parent date (vertical has same dates as subsections)
        date = get_date(ccx, node=parent_node, date_type=date_type)

    return date


def validate_date(year, month, day, hour, minute):
    """
    avoid corrupting db if bad dates come in
    """
    valid = True
    if year < 0:
        valid = False
    if month < 1 or month > 12:
        valid = False
    if day < 1 or day > 31:
        valid = False
    if hour < 0 or hour > 23:
        valid = False
    if minute < 0 or minute > 59:
        valid = False
    return valid


def parse_date(datestring):
    """
    Generate a UTC datetime.datetime object from a string of the form
    'YYYY-MM-DD HH:MM'.  If string is empty or `None`, returns `None`.
    """
    if datestring:
        date, time = datestring.split(' ')
        year, month, day = map(int, date.split('-'))
        hour, minute = map(int, time.split(':'))
        if validate_date(year, month, day, hour, minute):
            return datetime.datetime(
                year, month, day, hour, minute, tzinfo=pytz.UTC)

    return None


def get_ccx_for_coach(course, coach):
    """
    Looks to see if user is coach of a CCX for this course.  Returns the CCX or
    None.
    """
    ccxs = CustomCourseForEdX.objects.filter(
        course_id=course.id,
        coach=coach
    )
    # XXX: In the future, it would be nice to support more than one ccx per
    # coach per course.  This is a place where that might happen.
    if ccxs.exists():
        return ccxs[0]
    return None


def get_valid_student_email(identifier):
    """
    Helper function to get an user email from an identifier and validate it.

    In the UI a Coach can enroll users using both an email and an username.
    This function takes care of:
    - in case the identifier is an username, extracting the user object from
        the DB and then the associated email
    - validating the email

    Arguments:
        identifier (str): Username or email of the user to enroll

    Returns:
        str: A validated email for the user to enroll

    Raises:
        CCXUserValidationException: if the username is not found or the email
            is not valid.
    """
    user = email = None
    try:
        user = get_student_from_identifier(identifier)
    except User.DoesNotExist:
        email = identifier
    else:
        email = user.email
    try:
        validate_email(email)
    except ValidationError:
        raise CCXUserValidationException('Could not find a user with name or email "{0}" '.format(identifier))
    return email


def ccx_students_enrolling_center(action, identifiers, email_students, course_key, email_params):
    """
    Function to enroll/add or unenroll/revoke students.

    This function exists for backwards compatibility: in CCX there are
    two different views to manage students that used to implement
    a different logic. Now the logic has been reconciled at the point that
    this function can be used by both.
    The two different views can be merged after some UI refactoring.

    Arguments:
        action (str): type of action to perform (add, Enroll, revoke, Unenroll)
        identifiers (list): list of students username/email
        email_students (bool): Flag to send an email to students
        course_key (CCXLocator): a CCX course key
        email_params (dict): dictionary of settings for the email to be sent

    Returns:
        list: list of error
    """
    errors = []

    if action == 'Enroll' or action == 'add':
        ccx_course_overview = CourseOverview.get_from_id(course_key)
        for identifier in identifiers:
            if CourseEnrollment.objects.is_course_full(ccx_course_overview):
                error = _('The course is full: the limit is {max_student_enrollments_allowed}').format(
                    max_student_enrollments_allowed=ccx_course_overview.max_student_enrollments_allowed)
                log.info("%s", error)
                errors.append(error)
                break
            try:
                email = get_valid_student_email(identifier)
            except CCXUserValidationException as exp:
                log.info("%s", exp)
                errors.append("{0}".format(exp))
                continue
            enroll_email(course_key, email, auto_enroll=True, email_students=email_students, email_params=email_params)
    elif action == 'Unenroll' or action == 'revoke':
        for identifier in identifiers:
            try:
                email = get_valid_student_email(identifier)
            except CCXUserValidationException as exp:
                log.info("%s", exp)
                errors.append("{0}".format(exp))
                continue
            unenroll_email(course_key, email, email_students=email_students, email_params=email_params)
    return errors


def prep_course_for_grading(course, request):
    """Set up course module for overrides to function properly"""
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
        course.id, request.user, course, depth=2)
    course = get_module_for_descriptor(
        request.user, request, course, field_data_cache, course.id, course=course
    )

    course._field_data_cache = {}  # pylint: disable=protected-access
    course.set_grading_policy(course.grading_policy)


@contextmanager
def ccx_course(ccx_locator):
    """Create a context in which the course identified by course_locator exists
    """
    course = get_course_by_id(ccx_locator)
    yield course


def assign_coach_role_to_ccx(ccx_locator, user, master_course_id):
    """
    Check if user has ccx_coach role on master course then assign him coach role on ccx only
    if role is not already assigned. Because of this coach can open dashboard from master course
    as well as ccx.
    :param ccx_locator: CCX key
    :param user: User to whom we want to assign role.
    :param master_course_id: Master course key
    """
    coach_role_on_master_course = CourseCcxCoachRole(master_course_id)
    # check if user has coach role on master course
    if coach_role_on_master_course.has_user(user):
        # Check if user has coach role on ccx.
        role = CourseCcxCoachRole(ccx_locator)
        if not role.has_user(user):
            # assign user role coach on ccx
            with ccx_course(ccx_locator) as course:
                allow_access(course, user, "ccx_coach", send_email=False)


def is_email(identifier):
    """
    Checks if an `identifier` string is a valid email
    """
    try:
        validate_email(identifier)
    except ValidationError:
        return False
    return True
