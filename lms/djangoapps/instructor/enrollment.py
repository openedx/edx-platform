"""
Enrollment operations for use by instructor APIs.

Does not include any access control, be sure to check access before calling.
"""

import json
import logging
from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from django.utils.translation import override as override_language

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from courseware.models import StudentModule
from edxmako.shortcuts import render_to_string
from lang_pref import LANGUAGE_KEY

from submissions import api as sub_api  # installed from the edx-submissions repository
from student.models import anonymous_id_for_user
from openedx.core.djangoapps.user_api.models import UserPreference

from microsite_configuration import microsite
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger(__name__)


class EmailEnrollmentState(object):
    """ Store the complete enrollment state of an email in a class """
    def __init__(self, course_id, email):
        exists_user = User.objects.filter(email=email).exists()
        if exists_user:
            user = User.objects.get(email=email)
            mode, is_active = CourseEnrollment.enrollment_mode_for_user(user, course_id)
            # is_active is `None` if the user is not enrolled in the course
            exists_ce = is_active is not None and is_active
            full_name = user.profile.name
        else:
            mode = None
            exists_ce = False
            full_name = None
        ceas = CourseEnrollmentAllowed.objects.filter(course_id=course_id, email=email).all()
        exists_allowed = ceas.exists()
        state_auto_enroll = exists_allowed and ceas[0].auto_enroll

        self.user = exists_user
        self.enrollment = exists_ce
        self.allowed = exists_allowed
        self.auto_enroll = bool(state_auto_enroll)
        self.full_name = full_name
        self.mode = mode

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


def get_user_email_language(user):
    """
    Return the language most appropriate for writing emails to user. Returns
    None if the preference has not been set, or if the user does not exist.
    """
    # Calling UserPreference directly instead of get_user_preference because the user requesting the
    # information is not "user" and also may not have is_staff access.
    return UserPreference.get_value(user, LANGUAGE_KEY)


def enroll_email(course_id, student_email, auto_enroll=False, email_students=False, email_params=None, language=None):
    """
    Enroll a student by email.

    `student_email` is student's emails e.g. "foo@bar.com"
    `auto_enroll` determines what is put in CourseEnrollmentAllowed.auto_enroll
        if auto_enroll is set, then when the email registers, they will be
        enrolled in the course automatically.
    `email_students` determines if student should be notified of action by email.
    `email_params` parameters used while parsing email templates (a `dict`).
    `language` is the language used to render the email.

    returns two EmailEnrollmentState's
        representing state before and after the action.
    """
    previous_state = EmailEnrollmentState(course_id, student_email)
    enrollment_obj = None
    if previous_state.user:
        # if the student is currently unenrolled, don't enroll them in their
        # previous mode
        course_mode = u"honor"
        if previous_state.enrollment:
            course_mode = previous_state.mode

        enrollment_obj = CourseEnrollment.enroll_by_email(student_email, course_id, course_mode)
        if email_students:
            email_params['message'] = 'enrolled_enroll'
            email_params['email_address'] = student_email
            email_params['full_name'] = previous_state.full_name
            send_mail_to_student(student_email, email_params, language=language)
    else:
        cea, _ = CourseEnrollmentAllowed.objects.get_or_create(course_id=course_id, email=student_email)
        cea.auto_enroll = auto_enroll
        cea.save()
        if email_students:
            email_params['message'] = 'allowed_enroll'
            email_params['email_address'] = student_email
            send_mail_to_student(student_email, email_params, language=language)

    after_state = EmailEnrollmentState(course_id, student_email)

    return previous_state, after_state, enrollment_obj


def unenroll_email(course_id, student_email, email_students=False, email_params=None, language=None):
    """
    Unenroll a student by email.

    `student_email` is student's emails e.g. "foo@bar.com"
    `email_students` determines if student should be notified of action by email.
    `email_params` parameters used while parsing email templates (a `dict`).
    `language` is the language used to render the email.

    returns two EmailEnrollmentState's
        representing state before and after the action.
    """
    previous_state = EmailEnrollmentState(course_id, student_email)
    if previous_state.enrollment:
        CourseEnrollment.unenroll_by_email(student_email, course_id)
        if email_students:
            email_params['message'] = 'enrolled_unenroll'
            email_params['email_address'] = student_email
            email_params['full_name'] = previous_state.full_name
            send_mail_to_student(student_email, email_params, language=language)

    if previous_state.allowed:
        CourseEnrollmentAllowed.objects.get(course_id=course_id, email=student_email).delete()
        if email_students:
            email_params['message'] = 'allowed_unenroll'
            email_params['email_address'] = student_email
            # Since no User object exists for this student there is no "full_name" available.
            send_mail_to_student(student_email, email_params, language=language)

    after_state = EmailEnrollmentState(course_id, student_email)

    return previous_state, after_state


def send_beta_role_email(action, user, email_params):
    """
    Send an email to a user added or removed as a beta tester.

    `action` is one of 'add' or 'remove'
    `user` is the User affected
    `email_params` parameters used while parsing email templates (a `dict`).
    """
    if action == 'add':
        email_params['message'] = 'add_beta_tester'
        email_params['email_address'] = user.email
        email_params['full_name'] = user.profile.name

    elif action == 'remove':
        email_params['message'] = 'remove_beta_tester'
        email_params['email_address'] = user.email
        email_params['full_name'] = user.profile.name

    else:
        raise ValueError("Unexpected action received '{}' - expected 'add' or 'remove'".format(action))

    send_mail_to_student(user.email, email_params, language=get_user_email_language(user))


def reset_student_attempts(course_id, student, module_state_key, delete_module=False):
    """
    Reset student attempts for a problem. Optionally deletes all student state for the specified problem.

    In the previous instructor dashboard it was possible to modify/delete
    modules that were not problems. That has been disabled for safety.

    `student` is a User
    `problem_to_reset` is the name of a problem e.g. 'L2Node1'.
    To build the module_state_key 'problem/' and course information will be appended to `problem_to_reset`.

    Raises:
        ValueError: `problem_state` is invalid JSON.
        StudentModule.DoesNotExist: could not load the student module.
        submissions.SubmissionError: unexpected error occurred while resetting the score in the submissions API.

    """
    try:
        # A block may have children. Clear state on children first.
        block = modulestore().get_item(module_state_key)
        if block.has_children:
            for child in block.children:
                try:
                    reset_student_attempts(course_id, student, child, delete_module=delete_module)
                except StudentModule.DoesNotExist:
                    # If a particular child doesn't have any state, no big deal, as long as the parent does.
                    pass
    except ItemNotFoundError:
        log.warning("Could not find %s in modulestore when attempting to reset attempts.", module_state_key)

    # Reset the student's score in the submissions API
    # Currently this is used only by open assessment (ORA 2)
    # We need to do this *before* retrieving the `StudentModule` model,
    # because it's possible for a score to exist even if no student module exists.
    if delete_module:
        sub_api.reset_score(
            anonymous_id_for_user(student, course_id),
            course_id.to_deprecated_string(),
            module_state_key.to_deprecated_string(),
        )

    module_to_reset = StudentModule.objects.get(
        student_id=student.id,
        course_id=course_id,
        module_state_key=module_state_key
    )

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


def get_email_params(course, auto_enroll, secure=True):
    """
    Generate parameters used when parsing email templates.

    `auto_enroll` is a flag for auto enrolling non-registered students: (a `boolean`)
    Returns a dict of parameters
    """

    protocol = 'https' if secure else 'http'

    stripped_site_name = microsite.get_value(
        'SITE_NAME',
        settings.SITE_NAME
    )
    # TODO: Use request.build_absolute_uri rather than '{proto}://{site}{path}'.format
    # and check with the Services team that this works well with microsites
    registration_url = u'{proto}://{site}{path}'.format(
        proto=protocol,
        site=stripped_site_name,
        path=reverse('register_user')
    )
    course_url = u'{proto}://{site}{path}'.format(
        proto=protocol,
        site=stripped_site_name,
        path=reverse('course_root', kwargs={'course_id': course.id.to_deprecated_string()})
    )

    # We can't get the url to the course's About page if the marketing site is enabled.
    course_about_url = None
    if not settings.FEATURES.get('ENABLE_MKTG_SITE', False):
        course_about_url = u'{proto}://{site}{path}'.format(
            proto=protocol,
            site=stripped_site_name,
            path=reverse('about_course', kwargs={'course_id': course.id.to_deprecated_string()})
        )

    is_shib_course = uses_shib(course)

    # Composition of email
    email_params = {
        'site_name': stripped_site_name,
        'registration_url': registration_url,
        'course': course,
        'auto_enroll': auto_enroll,
        'course_url': course_url,
        'course_about_url': course_about_url,
        'is_shib_course': is_shib_course,
    }
    return email_params


def send_mail_to_student(student, param_dict, language=None):
    """
    Construct the email using templates and then send it.
    `student` is the student's email address (a `str`),

    `param_dict` is a `dict` with keys
    [
        `site_name`: name given to edX instance (a `str`)
        `registration_url`: url for registration (a `str`)
        `course_id`: id of course (a `str`)
        `auto_enroll`: user input option (a `str`)
        `course_url`: url of course (a `str`)
        `email_address`: email of student (a `str`)
        `full_name`: student full name (a `str`)
        `message`: type of email to send and template to use (a `str`)
        `is_shib_course`: (a `boolean`)
    ]

    `language` is the language used to render the email. If None the language
    of the currently-logged in user (that is, the user sending the email) will
    be used.

    Returns a boolean indicating whether the email was sent successfully.
    """

    # add some helpers and microconfig subsitutions
    if 'course' in param_dict:
        param_dict['course_name'] = param_dict['course'].display_name_with_default

    param_dict['site_name'] = microsite.get_value(
        'SITE_NAME',
        param_dict['site_name']
    )

    subject = None
    message = None

    # see if we are running in a microsite and that there is an
    # activation email template definition available as configuration, if so, then render that
    message_type = param_dict['message']

    email_template_dict = {
        'allowed_enroll': (
            'emails/enroll_email_allowedsubject.txt',
            'emails/enroll_email_allowedmessage.txt'
        ),
        'enrolled_enroll': (
            'emails/enroll_email_enrolledsubject.txt',
            'emails/enroll_email_enrolledmessage.txt'
        ),
        'allowed_unenroll': (
            'emails/unenroll_email_subject.txt',
            'emails/unenroll_email_allowedmessage.txt'
        ),
        'enrolled_unenroll': (
            'emails/unenroll_email_subject.txt',
            'emails/unenroll_email_enrolledmessage.txt'
        ),
        'add_beta_tester': (
            'emails/add_beta_tester_email_subject.txt',
            'emails/add_beta_tester_email_message.txt'
        ),
        'remove_beta_tester': (
            'emails/remove_beta_tester_email_subject.txt',
            'emails/remove_beta_tester_email_message.txt'
        ),
        'account_creation_and_enrollment': (
            'emails/enroll_email_enrolledsubject.txt',
            'emails/account_creation_and_enroll_emailMessage.txt'
        ),
    }

    subject_template, message_template = email_template_dict.get(message_type, (None, None))
    if subject_template is not None and message_template is not None:
        subject, message = render_message_to_string(
            subject_template, message_template, param_dict, language=language
        )

    if subject and message:
        # Remove leading and trailing whitespace from body
        message = message.strip()

        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        from_address = microsite.get_value(
            'email_from_address',
            settings.DEFAULT_FROM_EMAIL
        )

        send_mail(subject, message, from_address, [student], fail_silently=False)


def render_message_to_string(subject_template, message_template, param_dict, language=None):
    """
    Render a mail subject and message templates using the parameters from
    param_dict and the given language. If language is None, the platform
    default language is used.

    Returns two strings that correspond to the rendered, translated email
    subject and message.
    """
    with override_language(language):
        return get_subject_and_message(subject_template, message_template, param_dict)


def get_subject_and_message(subject_template, message_template, param_dict):
    """
    Return the rendered subject and message with the appropriate parameters.
    """
    subject = render_to_string(subject_template, param_dict)
    message = render_to_string(message_template, param_dict)
    return subject, message


def uses_shib(course):
    """
    Used to return whether course has Shibboleth as the enrollment domain

    Returns a boolean indicating if Shibboleth authentication is set for this course.
    """
    return course.enrollment_domain and course.enrollment_domain.startswith(settings.SHIBBOLETH_DOMAIN_PREFIX)
