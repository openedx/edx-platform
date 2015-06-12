"""
CCX Enrollment operations for use by Coach APIs.

Does not include any access control, be sure to check access before calling.
"""
import logging
from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail
from edxmako.shortcuts import render_to_string  # pylint: disable=import-error
from microsite_configuration import microsite  # pylint: disable=import-error
from xmodule.modulestore.django import modulestore
from xmodule.error_module import ErrorDescriptor
from ccx_keys.locator import CCXLocator

from .models import (
    CcxMembership,
    CcxFutureMembership,
)


log = logging.getLogger("edx.ccx")


class EmailEnrollmentState(object):
    """ Store the complete enrollment state of an email in a class """
    def __init__(self, ccx, email):
        exists_user = User.objects.filter(email=email).exists()
        if exists_user:
            user = User.objects.get(email=email)
            ccx_member = CcxMembership.objects.filter(ccx=ccx, student=user)
            in_ccx = ccx_member.exists()
            full_name = user.profile.name
        else:
            user = None
            in_ccx = False
            full_name = None
        self.user = exists_user
        self.member = user
        self.full_name = full_name
        self.in_ccx = in_ccx

    def __repr__(self):
        return "{}(user={}, member={}, in_ccx={})".format(
            self.__class__.__name__,
            self.user,
            self.member,
            self.in_ccx,
        )

    def to_dict(self):
        """ return dict with membership and ccx info """
        return {
            'user': self.user,
            'member': self.member,
            'in_ccx': self.in_ccx,
        }


def enroll_email(ccx, student_email, auto_enroll=False, email_students=False, email_params=None):
    """
    Send email to newly enrolled student
    """
    if email_params is None:
        email_params = get_email_params(ccx, True)
    previous_state = EmailEnrollmentState(ccx, student_email)

    if previous_state.user:
        user = User.objects.get(email=student_email)
        if not previous_state.in_ccx:
            membership = CcxMembership(
                ccx=ccx, student=user, active=True
            )
            membership.save()
        elif auto_enroll:
            # activate existing memberships
            membership = CcxMembership.objects.get(student=user, ccx=ccx)
            membership.active = True
            membership.save()
        if email_students:
            email_params['message'] = 'enrolled_enroll'
            email_params['email_address'] = student_email
            email_params['full_name'] = previous_state.full_name
            send_mail_to_student(student_email, email_params)
    else:
        membership = CcxFutureMembership(
            ccx=ccx, auto_enroll=auto_enroll, email=student_email
        )
        membership.save()
        if email_students:
            email_params['message'] = 'allowed_enroll'
            email_params['email_address'] = student_email
            send_mail_to_student(student_email, email_params)

    after_state = EmailEnrollmentState(ccx, student_email)

    return previous_state, after_state


def unenroll_email(ccx, student_email, email_students=False, email_params=None):
    """
    send email to unenrolled students
    """
    if email_params is None:
        email_params = get_email_params(ccx, True)
    previous_state = EmailEnrollmentState(ccx, student_email)

    if previous_state.in_ccx:
        CcxMembership.objects.get(
            ccx=ccx, student=previous_state.member
        ).delete()
        if email_students:
            email_params['message'] = 'enrolled_unenroll'
            email_params['email_address'] = student_email
            email_params['full_name'] = previous_state.full_name
            send_mail_to_student(student_email, email_params)
    else:
        if CcxFutureMembership.objects.filter(
                ccx=ccx, email=student_email).exists():
            CcxFutureMembership.objects.get(
                ccx=ccx, email=student_email
            ).delete()
        if email_students:
            email_params['message'] = 'allowed_unenroll'
            email_params['email_address'] = student_email
            send_mail_to_student(student_email, email_params)

    after_state = EmailEnrollmentState(ccx, student_email)

    return previous_state, after_state


def get_email_params(ccx, auto_enroll, secure=True):
    """
    get parameters for enrollment emails
    """
    protocol = 'https' if secure else 'http'

    stripped_site_name = microsite.get_value(
        'SITE_NAME',
        settings.SITE_NAME
    )
    registration_url = u'{proto}://{site}{path}'.format(
        proto=protocol,
        site=stripped_site_name,
        path=reverse('register_user')
    )
    course_url = u'{proto}://{site}{path}'.format(
        proto=protocol,
        site=stripped_site_name,
        path=reverse(
            'course_root',
            kwargs={'course_id': CCXLocator.from_course_locator(ccx.course_id, ccx.id)}
        )
    )

    course_about_url = None
    if not settings.FEATURES.get('ENABLE_MKTG_SITE', False):
        course_about_url = u'{proto}://{site}{path}'.format(
            proto=protocol,
            site=stripped_site_name,
            path=reverse(
                'about_course',
                kwargs={'course_id': CCXLocator.from_course_locator(ccx.course_id, ccx.id)}
            )
        )

    email_params = {
        'site_name': stripped_site_name,
        'registration_url': registration_url,
        'course': ccx,
        'auto_enroll': auto_enroll,
        'course_url': course_url,
        'course_about_url': course_about_url,
    }
    return email_params


def send_mail_to_student(student, param_dict):
    """
    Check parameters, set text template and send email to student
    """
    if 'course' in param_dict:
        param_dict['course_name'] = param_dict['course'].display_name

    param_dict['site_name'] = microsite.get_value(
        'SITE_NAME',
        param_dict['site_name']
    )

    subject = None
    message = None

    message_type = param_dict['message']

    email_template_dict = {
        'allowed_enroll': (
            'ccx/enroll_email_allowedsubject.txt',
            'ccx/enroll_email_allowedmessage.txt'
        ),
        'enrolled_enroll': (
            'ccx/enroll_email_enrolledsubject.txt',
            'ccx/enroll_email_enrolledmessage.txt'
        ),
        'allowed_unenroll': (
            'ccx/unenroll_email_subject.txt',
            'ccx/unenroll_email_allowedmessage.txt'
        ),
        'enrolled_unenroll': (
            'ccx/unenroll_email_subject.txt',
            'ccx/unenroll_email_enrolledmessage.txt'
        ),
    }

    subject_template, message_template = email_template_dict.get(
        message_type, (None, None)
    )
    if subject_template is not None and message_template is not None:
        subject = render_to_string(subject_template, param_dict)
        message = render_to_string(message_template, param_dict)

    if subject and message:
        message = message.strip()

        subject = ''.join(subject.splitlines())
        from_address = microsite.get_value(
            'email_from_address',
            settings.DEFAULT_FROM_EMAIL
        )

        send_mail(
            subject,
            message,
            from_address,
            [student],
            fail_silently=False
        )


def get_ccx_membership_triplets(user, course_org_filter, org_filter_out_set):
    """
    Get the relevant set of (CustomCourseForEdX, CcxMembership, Course)
    triplets to be displayed on a student's dashboard.
    """
    # only active memberships for now
    for membership in CcxMembership.memberships_for_user(user):
        ccx = membership.ccx
        store = modulestore()
        with store.bulk_operations(ccx.course_id):
            course = store.get_course(ccx.course_id)
            if course and not isinstance(course, ErrorDescriptor):
                # if we are in a Microsite, then filter out anything that is not
                # attributed (by ORG) to that Microsite
                if course_org_filter and course_org_filter != course.location.org:
                    continue
                # Conversely, if we are not in a Microsite, then let's filter out any enrollments
                # with courses attributed (by ORG) to Microsites
                elif course.location.org in org_filter_out_set:
                    continue

                # If, somehow, we've got a ccx that has been created for a
                # course with a deprecated ID, we must filter it out. Emit a
                # warning to the log so we can clean up.
                if course.location.deprecated:
                    log.warning(
                        "CCX %s exists for course %s with deprecated id",
                        ccx,
                        ccx.course_id
                    )
                    continue

                yield (ccx, membership, course)
            else:
                log.error("User {0} enrolled in {2} course {1}".format(  # pylint: disable=logging-format-interpolation
                    user.username, ccx.course_id, "broken" if course else "non-existent"
                ))
