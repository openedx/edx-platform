"""
This module provides date summary blocks for the Course Info
page. Each block gives information about a particular
course-run-specific date which will be displayed to the user.
"""
import crum
import datetime

from babel.dates import format_timedelta

from django.conf import settings
from django.urls import reverse
from django.utils.formats import date_format
from django.utils.functional import cached_property
from django.utils.translation import get_language, to_locale, ugettext_lazy
from django.utils.translation import ugettext as _
from lazy import lazy
from pytz import utc

from openedx.core.djangoapps.course_modes.models import CourseMode, get_cosmetic_verified_display_price
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.verify_student.models import VerificationDeadline
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.certificates.api import can_show_certificate_available_date_field
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.course_experience import CourseHomeMessages, UPGRADE_DEADLINE_MESSAGE
from student.models import CourseEnrollment

from .context_processor import user_timezone_locale_prefs


class DateSummary(object):
    """Base class for all date summary blocks."""

    # A consistent representation of the current time.
    _current_time = None

    @property
    def current_time(self):
        """
        Returns a consistent current time.
        """
        if self._current_time is None:
            self._current_time = datetime.datetime.now(utc)
        return self._current_time

    @property
    def css_class(self):
        """
        The CSS class of this summary. Indicates the type of information
        this summary block contains, and its urgency.
        """
        return ''

    @property
    def title(self):
        """The title of this summary."""
        return ''

    @property
    def description(self):
        """The detail text displayed by this summary."""
        return ''

    def register_alerts(self, request, course):
        """
        Registers any relevant course alerts given the current request.
        """
        pass

    @property
    def date(self):
        """This summary's date."""
        return None

    @property
    def date_format(self):
        """
        The format to display this date in. By default, displays like Jan
        01, 2015.
        """
        return u'%b %d, %Y'

    @property
    def link(self):
        """The location to link to for more information."""
        return ''

    @property
    def link_text(self):
        """The text of the link."""
        return ''

    def __init__(self, course, user, course_id=None):
        self.course = course
        self.user = user
        self.course_id = course_id or self.course.id

    @property
    def relative_datestring(self):
        """
        Return this block's date in a human-readable format. If the date
        is None, returns the empty string.
        """
        if self.date is None:
            return ''
        locale = to_locale(get_language())
        delta = self.date - self.current_time
        try:
            relative_date = format_timedelta(delta, locale=locale)
        # Babel doesn't have translations for Esperanto, so we get
        # a KeyError when testing translations with
        # ?preview-lang=eo. This should not happen with any other
        # languages. See https://github.com/python-babel/babel/issues/107
        except KeyError:
            relative_date = format_timedelta(delta)
        date_has_passed = delta.days < 0
        # Translators: 'absolute' is a date such as "Jan 01,
        # 2020". 'relative' is a fuzzy description of the time until
        # 'absolute'. For example, 'absolute' might be "Jan 01, 2020",
        # and if today were December 5th, 2020, 'relative' would be "1
        # month".
        date_format = _(u"{relative} ago - {absolute}") if date_has_passed else _(u"in {relative} - {absolute}")
        return date_format.format(
            relative=relative_date,
            absolute='{date}',
        )

    @property
    def is_enabled(self):
        """
        Whether or not this summary block should be shown.

        By default, the summary is only shown if its date is in the
        future.
        """
        if self.date is not None:
            return self.current_time.date() <= self.date.date()
        return False

    def deadline_has_passed(self):
        """
        Return True if a deadline (the date) exists, and has already passed.
        Returns False otherwise.
        """
        deadline = self.date
        return deadline is not None and deadline <= self.current_time

    @property
    def time_remaining_string(self):
        """
        Returns the time remaining as a localized string.
        """
        locale = to_locale(get_language())
        return format_timedelta(self.date - self.current_time, locale=locale)

    def date_html(self, date_format='shortDate'):
        """
        Returns a representation of the date as HTML.

        Note: this returns a span that will be localized on the client.
        """
        locale = to_locale(get_language())
        user_timezone = user_timezone_locale_prefs(crum.get_current_request())['user_timezone']
        return HTML(
            u'<span class="date localized-datetime" data-format="{date_format}" data-datetime="{date_time}"'
            u' data-timezone="{user_timezone}" data-language="{user_language}">'
            u'</span>'
        ).format(
            date_format=date_format,
            date_time=self.date,
            user_timezone=user_timezone,
            user_language=locale,
        )

    @property
    def long_date_html(self):
        """
        Returns a long representation of the date as HTML.

        Note: this returns a span that will be localized on the client.
        """
        return self.date_html(date_format='shortDate')

    @property
    def short_time_html(self):
        """
        Returns a short representation of the time as HTML.

        Note: this returns a span that will be localized on the client.
        """
        return self.date_html(date_format='shortTime')

    def __repr__(self):
        return u'DateSummary: "{title}" {date} is_enabled={is_enabled}'.format(
            title=self.title,
            date=self.date,
            is_enabled=self.is_enabled
        )


class TodaysDate(DateSummary):
    """
    Displays today's date.
    """
    css_class = 'todays-date'
    is_enabled = True

    # The date is shown in the title, no need to display it again.
    def get_context(self):
        context = super(TodaysDate, self).get_context()
        context['date'] = ''
        return context

    @property
    def date(self):
        return self.current_time

    @property
    def title(self):
        return 'current_datetime'


class CourseStartDate(DateSummary):
    """
    Displays the start date of the course.
    """
    css_class = 'start-date'
    title = ugettext_lazy('Course Starts')

    @property
    def date(self):
        return self.course.start

    def register_alerts(self, request, course):
        """
        Registers an alert if the course has not started yet.
        """
        is_enrolled = CourseEnrollment.get_enrollment(request.user, course.id)
        if not course.start or not is_enrolled:
            return
        days_until_start = (course.start - self.current_time).days
        if course.start > self.current_time:
            if days_until_start > 0:
                CourseHomeMessages.register_info_message(
                    request,
                    Text(_(
                        "Don't forget to add a calendar reminder!"
                    )),
                    title=Text(_(u"Course starts in {time_remaining_string} on {course_start_date}.")).format(
                        time_remaining_string=self.time_remaining_string,
                        course_start_date=self.long_date_html,
                    )
                )
            else:
                CourseHomeMessages.register_info_message(
                    request,
                    Text(_(u"Course starts in {time_remaining_string} at {course_start_time}.")).format(
                        time_remaining_string=self.time_remaining_string,
                        course_start_time=self.short_time_html,
                    )
                )


class CourseEndDate(DateSummary):
    """
    Displays the end date of the course.
    """
    css_class = 'end-date'
    title = ugettext_lazy('Course End')

    @property
    def is_enabled(self):
        return self.date is not None

    @property
    def description(self):
        if self.current_time <= self.date:
            mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_id)
            if is_active and CourseMode.is_eligible_for_certificate(mode):
                return _('To earn a certificate, you must complete all requirements before this date.')
            else:
                return _('After this date, course content will be archived.')
        return _('This course is archived, which means you can review course content but it is no longer active.')

    @property
    def date(self):
        return self.course.end

    def register_alerts(self, request, course):
        """
        Registers an alert if the end date is approaching.
        """
        is_enrolled = CourseEnrollment.get_enrollment(request.user, course.id)
        if not course.start or self.current_time < course.start or not is_enrolled:
            return
        days_until_end = (course.end - self.current_time).days
        if course.end > self.current_time and days_until_end <= settings.COURSE_MESSAGE_ALERT_DURATION_IN_DAYS:
            if days_until_end > 0:
                CourseHomeMessages.register_info_message(
                    request,
                    Text(self.description),
                    title=Text(_(u'This course is ending in {time_remaining_string} on {course_end_date}.')).format(
                        time_remaining_string=self.time_remaining_string,
                        course_end_date=self.long_date_html,
                    )
                )
            else:
                CourseHomeMessages.register_info_message(
                    request,
                    Text(self.description),
                    title=Text(_(u'This course is ending in {time_remaining_string} at {course_end_time}.')).format(
                        time_remaining_string=self.time_remaining_string,
                        course_end_time=self.short_time_html,
                    )
                )


class CertificateAvailableDate(DateSummary):
    """
    Displays the certificate available date of the course.
    """
    css_class = 'certificate-available-date'
    title = ugettext_lazy('Certificate Available')

    @property
    def active_certificates(self):
        return [
            certificate for certificate in self.course.certificates.get('certificates', [])
            if certificate.get('is_active', False)
        ]

    @property
    def is_enabled(self):
        return (
            can_show_certificate_available_date_field(self.course) and
            self.has_certificate_modes and
            self.date is not None and
            self.current_time <= self.date and
            len(self.active_certificates) > 0
        )

    @property
    def description(self):
        return _('Day certificates will become available for passing verified learners.')

    @property
    def date(self):
        return self.course.certificate_available_date

    @property
    def has_certificate_modes(self):
        return any([
            mode.slug for mode in CourseMode.modes_for_course(
                course_id=self.course.id, include_expired=True
            ) if mode.slug != CourseMode.AUDIT
        ])

    def register_alerts(self, request, course):
        """
        Registers an alert close to the certificate delivery date.
        """
        is_enrolled = CourseEnrollment.get_enrollment(request.user, course.id)
        if not is_enrolled or not self.is_enabled or course.end > self.current_time:
            return
        if self.date > self.current_time:
            CourseHomeMessages.register_info_message(
                request,
                Text(_(
                    u'If you have earned a certificate, you will be able to access it {time_remaining_string}'
                    u' from now. You will also be able to view your certificates on your {learner_profile_link}.'
                )).format(
                    time_remaining_string=self.time_remaining_string,
                    learner_profile_link=HTML(
                        u'<a href="{learner_profile_url}">{learner_profile_name}</a>'
                    ).format(
                        learner_profile_url=reverse('learner_profile', kwargs={'username': request.user.username}),
                        learner_profile_name=_('Learner Profile'),
                    ),
                ),
                title=Text(_('We are working on generating course certificates.'))
            )


def verified_upgrade_deadline_link(user, course=None, course_id=None):
    """
    Format the correct verified upgrade link for the specified ``user``
    in a course.

    One of ``course`` or ``course_id`` must be supplied. If both are specified,
    ``course`` will take priority.

    Arguments:
        user (:class:`~django.contrib.auth.models.User`): The user to display
            the link for.
        course (:class:`.CourseOverview`): The course to render a link for.
        course_id (:class:`.CourseKey`): The course_id of the course to render for.

    Returns:
        The formatted link that will allow the user to upgrade to verified
        in this course.
    """
    if course is not None:
        course_id = course.id
    return EcommerceService().upgrade_url(user, course_id)


def verified_upgrade_link_is_valid(enrollment=None):
    """
    Return whether this enrollment can be upgraded.

    Arguments:
        enrollment (:class:`.CourseEnrollment`): The enrollment under consideration.
            If None, then the enrollment is considered to be upgradeable.
    """
    # Return `true` if user is not enrolled in course
    if enrollment is None:
        return False

    upgrade_deadline = enrollment.upgrade_deadline

    if upgrade_deadline is None:
        return False

    if datetime.datetime.now(utc).date() > upgrade_deadline.date():
        return False

    # Show the summary if user enrollment is in which allow user to upsell
    return enrollment.is_active and enrollment.mode in CourseMode.UPSELL_TO_VERIFIED_MODES


class VerifiedUpgradeDeadlineDate(DateSummary):
    """
    Displays the date before which learners must upgrade to the
    Verified track.
    """
    css_class = 'verified-upgrade-deadline'
    link_text = ugettext_lazy('Upgrade to Verified Certificate')

    @property
    def link(self):
        return verified_upgrade_deadline_link(self.user, self.course, self.course_id)

    @cached_property
    def enrollment(self):
        return CourseEnrollment.get_enrollment(self.user, self.course_id)

    @property
    def is_enabled(self):
        """
        Whether or not this summary block should be shown.

        By default, the summary is only shown if it has date and the date is in the
        future and the user's enrollment is in upsell modes
        """
        is_enabled = super(VerifiedUpgradeDeadlineDate, self).is_enabled
        if not is_enabled:
            return False

        return verified_upgrade_link_is_valid(self.enrollment)

    @lazy
    def date(self):
        if self.enrollment:
            return self.enrollment.upgrade_deadline
        else:
            return None

    @property
    def title(self):
        dynamic_deadline = self._dynamic_deadline()
        if dynamic_deadline is not None:
            return _('Upgrade to Verified Certificate')

        return _('Verification Upgrade Deadline')

    def _dynamic_deadline(self):
        if not self.enrollment:
            return None

        return self.enrollment.dynamic_upgrade_deadline

    @property
    def description(self):
        dynamic_deadline = self._dynamic_deadline()
        if dynamic_deadline is not None:
            return _('Don\'t miss the opportunity to highlight your new knowledge and skills by earning a verified'
                     ' certificate.')

        return _('You are still eligible to upgrade to a Verified Certificate! '
                 'Pursue it to highlight the knowledge and skills you gain in this course.')

    @property
    def relative_datestring(self):
        dynamic_deadline = self._dynamic_deadline()
        if dynamic_deadline is None:
            return super(VerifiedUpgradeDeadlineDate, self).relative_datestring

        if self.date is None or self.deadline_has_passed():
            return ' '

        # Translators: This describes the time by which the user
        # should upgrade to the verified track. 'date' will be
        # their personalized verified upgrade deadline formatted
        # according to their locale.
        return _(u'by {date}')

    def register_alerts(self, request, course):
        """
        Registers an alert if the verification deadline is approaching.
        """
        upgrade_price = get_cosmetic_verified_display_price(course)
        if not UPGRADE_DEADLINE_MESSAGE.is_enabled(course.id) or not self.is_enabled or not upgrade_price:
            return
        days_left_to_upgrade = (self.date - self.current_time).days
        if self.date > self.current_time and days_left_to_upgrade <= settings.COURSE_MESSAGE_ALERT_DURATION_IN_DAYS:
            upgrade_message = _(
                u"Don't forget, you have {time_remaining_string} left to upgrade to a Verified Certificate."
            ).format(time_remaining_string=self.time_remaining_string)
            if self._dynamic_deadline() is not None:
                upgrade_message = _(
                    u"Don't forget to upgrade to a verified certificate by {localized_date}."
                ).format(localized_date=date_format(self.date))
            CourseHomeMessages.register_info_message(
                request,
                Text(_(
                    'In order to qualify for a certificate, you must meet all course grading '
                    'requirements, upgrade before the course deadline, and successfully verify '
                    u'your identity on {platform_name} if you have not done so already.{button_panel}'
                )).format(
                    platform_name=settings.PLATFORM_NAME,
                    button_panel=HTML(
                        '<div class="message-actions">'
                        '<a class="btn btn-upgrade"'
                        'data-creative="original_message" data-position="course_message"'
                        'href="{upgrade_url}">{upgrade_label}</a>'
                        '</div>'
                    ).format(
                        upgrade_url=self.link,
                        upgrade_label=Text(_(u'Upgrade ({upgrade_price})')).format(upgrade_price=upgrade_price),
                    )
                ),
                title=Text(upgrade_message)
            )


class VerificationDeadlineDate(DateSummary):
    """
    Displays the date by which the user must complete the verification
    process.
    """

    @property
    def css_class(self):
        base_state = 'verification-deadline'
        if self.deadline_has_passed():
            return base_state + '-passed'
        elif self.must_retry():
            return base_state + '-retry'
        else:
            return base_state + '-upcoming'

    @property
    def link_text(self):
        return self.link_table[self.css_class][0]

    @property
    def link(self):
        return self.link_table[self.css_class][1]

    @property
    def link_table(self):
        """Maps verification state to a tuple of link text and location."""
        return {
            'verification-deadline-passed': (_('Learn More'), ''),
            'verification-deadline-retry': (_('Retry Verification'), reverse('verify_student_reverify')),
            'verification-deadline-upcoming': (
                _('Verify My Identity'),
                reverse('verify_student_verify_now', args=(self.course_id,))
            )
        }

    @property
    def title(self):
        if self.deadline_has_passed():
            return _('Missed Verification Deadline')
        return _('Verification Deadline')

    @property
    def description(self):
        if self.deadline_has_passed():
            return _(
                "Unfortunately you missed this course's deadline for"
                " a successful verification."
            )
        return _(
            "You must successfully complete verification before"
            " this date to qualify for a Verified Certificate."
        )

    @lazy
    def date(self):
        return VerificationDeadline.deadline_for_course(self.course_id)

    @lazy
    def is_enabled(self):
        if self.date is None:
            return False
        (mode, is_active) = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_id)
        if is_active and mode == 'verified':
            return self.verification_status in ('expired', 'none', 'must_reverify')
        return False

    @lazy
    def verification_status(self):
        """Return the verification status for this user."""
        verification_status = IDVerificationService.user_status(self.user)
        return verification_status['status']

    def must_retry(self):
        """Return True if the user must re-submit verification, False otherwise."""
        return self.verification_status == 'must_reverify'
