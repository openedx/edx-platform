"""
This module provides date summary blocks for the Course Info
page. Each block gives information about a particular
course-run-specific date which will be displayed to the user.
"""
from datetime import datetime

from babel.dates import format_timedelta
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils.translation import to_locale, get_language
from edxmako.shortcuts import render_to_string
from lazy import lazy
import pytz

from course_modes.models import CourseMode
from verify_student.models import VerificationDeadline, SoftwareSecurePhotoVerification
from student.models import CourseEnrollment


class DateSummary(object):
    """Base class for all date summary blocks."""

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
        return '%b %d, %Y'

    @property
    def link(self):
        """The location to link to for more information."""
        return ''

    @property
    def link_text(self):
        """The text of the link."""
        return ''

    def __init__(self, course, user):
        self.course = course
        self.user = user

    def get_context(self):
        """Return the template context used to render this summary block."""
        date = ''
        if self.date is not None:
            # Translators: relative_date is a fuzzy description of the
            # time from now until absolute_date. For example,
            # absolute_date might be "Jan 01, 2020", and if today were
            # December 5th, 2020, relative_date would be "1 month".
            locale = to_locale(get_language())
            try:
                relative_date = format_timedelta(self.date - datetime.now(pytz.UTC), locale=locale)
            # Babel doesn't have translations for Esperanto, so we get
            # a KeyError when testing translations with
            # ?preview-lang=eo. This should not happen with any other
            # languages. See https://github.com/python-babel/babel/issues/107
            except KeyError:
                relative_date = format_timedelta(self.date - datetime.now(pytz.UTC))
            date = _("in {relative_date} - {absolute_date}").format(
                relative_date=relative_date,
                absolute_date=self.date.strftime(self.date_format),
            )
        return {
            'title': self.title,
            'date': date,
            'description': self.description,
            'css_class': self.css_class,
            'link': self.link,
            'link_text': self.link_text,
        }

    def render(self):
        """
        Return an HTML representation of this summary block.
        """
        return render_to_string('courseware/date_summary.html', self.get_context())

    @property
    def is_enabled(self):
        """
        Whether or not this summary block should be shown.

        By default, the summary is only shown if its date is in the
        future.
        """
        if self.date is not None:
            return datetime.now(pytz.UTC) <= self.date
        return False

    def __repr__(self):
        return 'DateSummary: "{title}" {date} is_enabled={is_enabled}'.format(
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
    date_format = '%b %d, %Y (%H:%M {utc})'.format(utc=_('UTC'))

    # The date is shown in the title, no need to display it again.
    def get_context(self):
        context = super(TodaysDate, self).get_context()
        context['date'] = ''
        return context

    @property
    def date(self):
        return datetime.now(pytz.UTC)

    @property
    def title(self):
        return _('Today is {date}').format(date=datetime.now(pytz.UTC).strftime(self.date_format))


class CourseStartDate(DateSummary):
    """
    Displays the start date of the course.
    """
    css_class = 'start-date'
    title = _('Course Starts')

    @property
    def date(self):
        return self.course.start


class CourseEndDate(DateSummary):
    """
    Displays the end date of the course.
    """
    css_class = 'end-date'
    title = _('Course End')

    @property
    def is_enabled(self):
        return self.date is not None

    @property
    def description(self):
        if datetime.now(pytz.UTC) <= self.date:
            return _('To earn a certificate, you must complete all requirements before this date.')
        return _('This course is archived, which means you can review course content but it is no longer active.')

    @property
    def date(self):
        return self.course.end


class VerifiedUpgradeDeadlineDate(DateSummary):
    """
    Displays the date before which learners must upgrade to the
    Verified track.
    """
    css_class = 'verified-upgrade-deadline'
    title = _('Verification Upgrade Deadline')
    description = _('You are still eligible to upgrade to a Verified Certificate!')
    link_text = _('Upgrade to Verified Certificate')

    @property
    def link(self):
        return reverse('verify_student_upgrade_and_verify', args=(self.course.id,))

    @lazy
    def date(self):
        try:
            verified_mode = CourseMode.objects.get(
                course_id=self.course.id, mode_slug=CourseMode.VERIFIED
            )
            return verified_mode.expiration_datetime
        except CourseMode.DoesNotExist:
            return None


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
                reverse('verify_student_verify_now', args=(self.course.id,))
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
        return VerificationDeadline.deadline_for_course(self.course.id)

    @lazy
    def is_enabled(self):
        if self.date is None:
            return False
        (mode, is_active) = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
        if is_active and mode == 'verified':
            return self.verification_status in ('expired', 'none', 'must_reverify')
        return False

    @lazy
    def verification_status(self):
        """Return the verification status for this user."""
        return SoftwareSecurePhotoVerification.user_status(self.user)[0]

    def deadline_has_passed(self):
        """
        Return True if a verification deadline exists, and has already passed.
        """
        deadline = self.date
        return deadline is not None and deadline <= datetime.now(pytz.UTC)

    def must_retry(self):
        """Return True if the user must re-submit verification, False otherwise."""
        return self.verification_status == 'must_reverify'
