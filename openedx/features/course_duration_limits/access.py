# -*- coding: utf-8 -*-
"""
Contains code related to computing content gating course duration limits
and course access based on these limits.
"""


from datetime import timedelta

import six
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from edx_django_utils.cache import RequestCache
from web_fragments.fragment import Fragment

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.access_response import AccessError
from lms.djangoapps.courseware.access_utils import ACCESS_GRANTED
from lms.djangoapps.courseware.utils import verified_upgrade_deadline_link
from lms.djangoapps.courseware.masquerade import get_course_masquerade, is_masquerading_as_specific_student
from openedx.core.djangoapps.catalog.utils import get_course_run_details
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_date_signals.utils import get_expected_duration
from openedx.core.djangolib.markup import HTML
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.util.date_utils import strftime_localized

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


def get_user_course_duration(user, course):
    """
    Return a timedelta measuring the duration of the course for a particular user.

    Business Logic:
      - Course access duration is bounded by the min and max duration.
      - If course fields are missing, default course access duration to MIN_DURATION.
    """
    if not CourseDurationLimitConfig.enabled_for_enrollment(user, course):
        return None

    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if enrollment is None or enrollment.mode != CourseMode.AUDIT:
        return None

    verified_mode = CourseMode.verified_mode_for_course(course=course, include_expired=True)
    if not verified_mode:
        return None

    return get_expected_duration(course.id)


def get_user_course_expiration_date(user, course):
    """
    Return expiration date for given user course pair.
    Return None if the course does not expire.

    Business Logic:
      - Course access duration is bounded by the min and max duration.
      - If course fields are missing, default course access duration to MIN_DURATION.
    """
    access_duration = get_user_course_duration(user, course)
    if access_duration is None:
        return None

    enrollment = CourseEnrollment.get_enrollment(user, course.id)
    if enrollment is None or enrollment.mode != CourseMode.AUDIT:
        return None

    # We reset schedule.start in order to change a user's computed deadlines.
    # But their expiration date shouldn't change when we adjust their schedule (they don't
    # get additional time), so we need to based the expiration date on a fixed start date.
    content_availability_date = max(enrollment.created, course.start)

    return content_availability_date + access_duration


def check_course_expired(user, course):
    """
    Check if the course expired for the user.
    """
    # masquerading course staff should always have access
    if get_course_masquerade(user, course.id):
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
                a_open=HTML(u'<a id="FBE_banner" href="{upgrade_link}">').format(
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
        return generate_fragment_from_message(message)


def generate_fragment_from_message(message):
    return Fragment(HTML(u"""\
            <div class="course-expiration-message">{}</div>
        """).format(message))


def generate_course_expired_fragment_from_key(user, course_key):
    """
    Like `generate_course_expired_fragment`, but using a CourseKey instead of
    a CourseOverview and using request-level caching.

    Either returns WebFragment to inject XBlock content into, or None if we
    shouldn't show a course expired message for this user.
    """
    request_cache = RequestCache('generate_course_expired_fragment_from_key')
    cache_key = u'message:{},{}'.format(user.id, course_key)
    cache_response = request_cache.get_cached_response(cache_key)
    if cache_response.is_found:
        cached_message = cache_response.value
        # In this case, there is no message to display.
        if cached_message is None:
            return None
        return generate_fragment_from_message(cached_message)

    course = CourseOverview.get_from_id(course_key)
    message = generate_course_expired_message(user, course)
    request_cache.set(cache_key, message)
    if message is None:
        return None

    return generate_fragment_from_message(message)


def course_expiration_wrapper(user, block, view, frag, context):  # pylint: disable=W0613
    """
    An XBlock wrapper that prepends a message to the beginning of a vertical if
    a user's course is about to expire.
    """
    if block.category != "vertical":
        return frag

    course_expiration_fragment = generate_course_expired_fragment_from_key(
        user, block.course_id
    )
    if not course_expiration_fragment:
        return frag

    # Course content must be escaped to render correctly due to the way the
    # way the XBlock rendering works. Transforming the safe markup to unicode
    # escapes correctly.
    course_expiration_fragment.content = six.text_type(course_expiration_fragment.content)

    course_expiration_fragment.add_content(frag.content)
    course_expiration_fragment.add_fragment_resources(frag)

    return course_expiration_fragment
