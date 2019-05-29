# -*- coding: utf-8 -*-
"""
Contains code related to computing content gating course duration limits
and course access based on these limits.
"""
from __future__ import absolute_import

from datetime import timedelta

import six
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.access_response import AccessError
from lms.djangoapps.courseware.access_utils import ACCESS_GRANTED
from lms.djangoapps.courseware.date_summary import verified_upgrade_deadline_link
from lms.djangoapps.courseware.masquerade import get_course_masquerade, is_masquerading_as_specific_student
from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangolib.markup import HTML
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from student.models import CourseEnrollment
from util.date_utils import strftime_localized

MIN_DURATION = timedelta(weeks=4)
MAX_DURATION = timedelta(weeks=18)
EXPIRATION_DATE_FORMAT_STR = u'%b %-d, %Y'


class AuditExpiredError(AccessError):
    """
    Access denied because the user's audit timespan has expired
    """
    def __init__(self, user, course, expiration_date):
        error_code = "audit_expired"
        developer_message = u"User {} had access to {} until {}".format(user, course, expiration_date)
        expiration_date = strftime_localized(expiration_date, EXPIRATION_DATE_FORMAT_STR)
        user_message = _(u"Access expired on {expiration_date}").format(expiration_date=expiration_date)
        try:
            course_name = course.display_name_with_default
            additional_context_user_message = _(u"Access to {course_name} expired on {expiration_date}").format(
                course_name=course_name,
                expiration_date=expiration_date
            )
        except CourseOverview.DoesNotExist:
            additional_context_user_message = _(u"Access to the course you were looking"
                                                u" for expired on {expiration_date}").format(
                expiration_date=expiration_date
            )
        super(AuditExpiredError, self).__init__(error_code, developer_message, user_message,
                                                additional_context_user_message)


def get_user_course_expiration_date(user, course):
    """
    Return expiration date for given user course pair.
    Return None if the course does not expire.

    Business Logic:
      - Course access duration is bounded by the min and max duration.
      - If course fields are missing, default course access duration to MIN_DURATION.
    """
    access_duration = MIN_DURATION

    verified_mode = CourseMode.verified_mode_for_course(course=course, include_expired=True)

    if not verified_mode:
        return None

    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if enrollment is None or enrollment.mode != CourseMode.AUDIT:
        return None

    try:
        # Content availability date is equivalent to max(enrollment date, course start date)
        # for most people. Using the schedule date will provide flexibility to deal with
        # more complex business rules in the future.
        content_availability_date = enrollment.schedule.start
        # We have anecdotally observed a case where the schedule.start was
        # equal to the course start, but should have been equal to the enrollment start
        # https://openedx.atlassian.net/browse/PROD-58
        # This section is meant to address that case
        if enrollment.created and course.start:
            if (content_availability_date.date() == course.start.date() and
               course.start < enrollment.created < timezone.now()):
                content_availability_date = enrollment.created
    except CourseEnrollment.schedule.RelatedObjectDoesNotExist:
        content_availability_date = max(enrollment.created, course.start)

    # The user course expiration date is the content availability date
    # plus the weeks_to_complete field from course-discovery.
    discovery_course_details = get_course_run_details(course.id, ['weeks_to_complete'])
    expected_weeks = discovery_course_details.get('weeks_to_complete')
    if expected_weeks:
        access_duration = timedelta(weeks=expected_weeks)

    # Course access duration is bounded by the min and max duration.
    access_duration = max(MIN_DURATION, min(MAX_DURATION, access_duration))

    return content_availability_date + access_duration


def check_course_expired(user, course):
    """
    Check if the course expired for the user.
    """
    # masquerading course staff should always have access
    if get_course_masquerade(user, course.id):
        return ACCESS_GRANTED

    if not CourseDurationLimitConfig.enabled_for_enrollment(user=user, course_key=course.id):
        return ACCESS_GRANTED

    expiration_date = get_user_course_expiration_date(user, course)
    if expiration_date and timezone.now() > expiration_date:
        return AuditExpiredError(user, course, expiration_date)

    return ACCESS_GRANTED


def get_date_string():
    # Creating this method to allow unit testing an issue where this string was missing the unicode prefix
    return u'<span class="localized-datetime" data-format="shortDate" \
        data-datetime="{formatted_date}" data-language="{language}">{formatted_date_localized}</span>'


def generate_course_expired_message(user, course):
    """
    Generate the message for the user course expiration date if it exists.
    """
    if not CourseDurationLimitConfig.enabled_for_enrollment(user=user, course_key=course.id):
        return

    expiration_date = get_user_course_expiration_date(user, course)
    if not expiration_date:
        return

    if is_masquerading_as_specific_student(user, course.id) and timezone.now() > expiration_date:
        upgrade_message = _('This learner does not have access to this course. '
                            u'Their access expired on {expiration_date}.')
        return HTML(upgrade_message).format(
            expiration_date=strftime_localized(expiration_date, EXPIRATION_DATE_FORMAT_STR)
        )
    else:
        enrollment = CourseEnrollment.get_enrollment(user, course.id)
        if enrollment is None:
            return

        upgrade_deadline = enrollment.upgrade_deadline
        now = timezone.now()
        course_upgrade_deadline = enrollment.course_upgrade_deadline
        if (not upgrade_deadline) or (upgrade_deadline < now):
            upgrade_deadline = course_upgrade_deadline

        expiration_message = _(u'{strong_open}Audit Access Expires {expiration_date}{strong_close}'
                               u'{line_break}You lose all access to this course, including your progress, on '
                               u'{expiration_date}.')
        upgrade_deadline_message = _(u'{line_break}Upgrade by {upgrade_deadline} to get unlimited access to the course '
                                     u'as long as it exists on the site. {a_open}Upgrade now{sronly_span_open} to '
                                     u'retain access past {expiration_date}{span_close}{a_close}')
        full_message = expiration_message
        if upgrade_deadline and now < upgrade_deadline:
            full_message += upgrade_deadline_message
            using_upgrade_messaging = True
        else:
            using_upgrade_messaging = False

        language = get_language()
        date_string = get_date_string()
        formatted_expiration_date = date_string.format(
            language=language,
            formatted_date=expiration_date.strftime("%Y-%m-%d"),
            formatted_date_localized=strftime_localized(expiration_date, EXPIRATION_DATE_FORMAT_STR)
        )
        if using_upgrade_messaging:
            formatted_upgrade_deadline = date_string.format(
                language=language,
                formatted_date=upgrade_deadline.strftime("%Y-%m-%d"),
                formatted_date_localized=strftime_localized(upgrade_deadline, EXPIRATION_DATE_FORMAT_STR)
            )

            return HTML(full_message).format(
                a_open=HTML(u'<a href="{upgrade_link}">').format(
                    upgrade_link=verified_upgrade_deadline_link(user=user, course=course)
                ),
                sronly_span_open=HTML('<span class="sr-only">'),
                span_close=HTML('</span>'),
                a_close=HTML('</a>'),
                expiration_date=HTML(formatted_expiration_date),
                strong_open=HTML('<strong>'),
                strong_close=HTML('</strong>'),
                line_break=HTML('<br>'),
                upgrade_deadline=HTML(formatted_upgrade_deadline)
            )

        else:
            return HTML(full_message).format(
                span_close=HTML('</span>'),
                expiration_date=HTML(formatted_expiration_date),
                strong_open=HTML('<strong>'),
                strong_close=HTML('</strong>'),
                line_break=HTML('<br>'),
            )


def generate_course_expired_fragment(user, course):
    message = generate_course_expired_message(user, course)
    if message:
        return Fragment(HTML(u"""\
            <div class="course-expiration-message">{}</div>
        """).format(message))


def course_expiration_wrapper(user, block, view, frag, context):  # pylint: disable=W0613
    """
    An XBlock wrapper that prepends a message to the beginning of a vertical if
    a user's course is about to expire.
    """
    if block.category != "vertical":
        return frag

    course = CourseOverview.get_from_id(block.course_id)
    course_expiration_fragment = generate_course_expired_fragment(user, course)

    if not course_expiration_fragment:
        return frag

    # Course content must be escaped to render correctly due to the way the
    # way the XBlock rendering works. Transforming the safe markup to unicode
    # escapes correctly.
    course_expiration_fragment.content = six.text_type(course_expiration_fragment.content)

    course_expiration_fragment.add_content(frag.content)
    course_expiration_fragment.add_fragment_resources(frag)

    return course_expiration_fragment
