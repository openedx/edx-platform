"""
POC Enrollment operations for use by Coach APIs.

Does not include any access control, be sure to check access before calling.
"""

import json
from django.contrib.auth.models import User
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail

from courseware.courses import get_course_about_section
from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_string
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from microsite_configuration import microsite

from pocs.models import (
    PersonalOnlineCourse,
    PocMembership,
    PocFutureMembership,
)


class EmailEnrollmentState(object):
    """ Store the complete enrollment state of an email in a class """
    def __init__(self, poc, email):
        exists_user = User.objects.filter(email=email).exists()
        if exists_user:
            user = User.objects.get(email=email)
            poc_member = PocMembership.objects.filter(poc=poc, student=user)
            in_poc = poc_member.exists()
            full_name = user.profile.name
        else:
            user = None
            in_poc = False
            full_name = None
        self.user = exists_user
        self.member = user
        self.full_name = full_name
        self.in_poc = in_poc

    def __repr__(self):
        return "{}(user={}, member={}, in_poc={}".format(
            self.__class__.__name__,
            self.user,
            self.member,
            self.in_poc,
        )

    def to_dict(self):
        return {
            'user': self.user,
            'member': self.member,
            'in_poc': self.in_poc,
        }


def enroll_email(poc, student_email, auto_enroll=False, email_students=False, email_params=None):
    if email_params is None:
        email_params = get_email_params(poc, True)
    previous_state = EmailEnrollmentState(poc, student_email)

    if previous_state.user:
        if not previous_state.in_poc:
            user = User.objects.get(email=student_email)
            membership = PocMembership(poc=poc, student=user)
            membership.save()
        if email_students:
            email_params['message'] = 'enrolled_enroll'
            email_params['email_address'] = student_email
            email_params['full_name'] = previous_state.full_name
            send_mail_to_student(student_email, email_params)
    else:
        membership = PocFutureMembership(poc=poc, email=student_email)
        membership.save()
        if email_students:
            email_params['message'] = 'allowed_enroll'
            email_params['email_address'] = student_email
            send_mail_to_student(student_email, email_params)

    after_state = EmailEnrollmentState(poc, student_email)

    return previous_state, after_state


def unenroll_email(poc, student_email, email_students=False, email_params=None):
    if email_params is None:
        email_params = get_email_params(poc, True)
    previous_state = EmailEnrollmentState(poc, student_email)

    if previous_state.in_poc:
        PocMembership.objects.get(
            poc=poc, student=previous_state.member
        ).delete()
        if email_students:
            email_params['message'] = 'enrolled_unenroll'
            email_params['email_address'] = student_email
            email_params['full_name'] = previous_state.full_name
            send_mail_to_student(student_email, email_params)
    else:
        if PocFutureMembership.objects.filter(
            poc=poc, email=student_email
        ).exists():
            PocFutureMembership.objects.get(
                poc=poc, email=student_email
            ).delete()
        if email_students:
            email_params['message'] = 'allowed_unenroll'
            email_params['email_address'] = student_email
            send_mail_to_student(student_email, email_params)

    after_state = EmailEnrollmentState(poc, student_email)

    return previous_state, after_state


def get_email_params(poc, auto_enroll, secure=True):
    protocol = 'https' if secure else 'http'
    course_id = poc.course_id

    stripped_site_name = microsite.get_value(
        'SITE_NAME',
        settings.SITE_NAME
    )
    registration_url = u'{proto}://{site}{path}'.format(
        proto=protocol,
        site=stripped_site_name,
        path=reverse('student.views.register_user')
    )
    course_url = u'{proto}://{site}{path}'.format(
        proto=protocol,
        site=stripped_site_name,
        path=reverse(
            'course_root',
            kwargs={'course_id': course_id.to_deprecated_string()}
        )
    )

    course_about_url = None
    if not settings.FEATURES.get('ENABLE_MKTG_SITE', False):
        course_about_url = u'{proto}://{site}{path}'.format(
            proto=protocol,
            site=stripped_site_name,
            path=reverse(
                'about_course',
                kwargs={'course_id': course_id.to_deprecated_string()}
            )
        )

    email_params = {
        'site_name': stripped_site_name,
        'registration_url': registration_url,
        'course': poc,
        'auto_enroll': auto_enroll,
        'course_url': course_url,
        'course_about_url': course_about_url,
    }
    return email_params


def send_mail_to_student(student, param_dict):
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
            'pocs/enroll_email_allowedsubject.txt',
            'pocs/enroll_email_allowedmessage.txt'
        ),
        'enrolled_enroll': (
            'pocs/enroll_email_enrolledsubject.txt',
            'pocs/enroll_email_enrolledmessage.txt'
        ),
        'allowed_unenroll': (
            'pocs/unenroll_email_subject.txt',
            'pocs/unenroll_email_allowedmessage.txt'
        ),
        'enrolled_unenroll': (
            'pocs/unenroll_email_subject.txt',
            'pocs/unenroll_email_enrolledmessage.txt'
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


def get_all_pocs_for_user(user):
    """return all POCS to which the user is registered

    Returns a list of dicts: {
        poc_name: <formatted title of POC course>
        poc_url: <url to view this POC>
    }
    """
    if user.is_anonymous():
        return []
    active_poc_memberships = PocMembership.objects.filter(
        student=user, active__exact=True
    )
    memberships = []
    for membership in active_poc_memberships:
        course = get_course_by_id(membership.poc.course_id)
        title = 'POC: {}'.format(get_course_about_section(course, 'title'))
        url = reverse(
            'switch_active_poc',
            args=[course.id.to_deprecated_string(), membership.poc.id]
        )
        memberships.append({
            'poc_name': title,
            'poc_url': url
        })
    return memberships
