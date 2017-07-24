"""
View logic for handling course messages.
"""

from babel.dates import format_date, format_timedelta
from datetime import datetime

from courseware.courses import get_course_with_access
from django.template.loader import render_to_string
from django.utils.http import urlquote_plus
from django.utils.timezone import UTC
from django.utils.translation import get_language, to_locale
from django.utils.translation import ugettext as _
from openedx.core.djangolib.markup import Text, HTML
from opaque_keys.edx.keys import CourseKey
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.features.course_experience import CourseHomeMessages


class CourseHomeMessageFragmentView(EdxFragmentView):
    """
    A fragment that displays a course message with an alert and call
    to action for three types of users:

    1) Not logged in users are given a link to sign in or register.
    2) Unenrolled users are given a link to enroll.
    3) Enrolled users who get to the page before the course start date
    are given the option to add the start date to their calendar.

    This fragment requires a user_access map as follows:

    user_access = {
        'is_anonymous': True if the user is logged in, False otherwise
        'is_enrolled': True if the user is enrolled in the course, False otherwise
        'is_staff': True if the user is a staff member of the course, False otherwise
    }
    """
    def render_to_fragment(self, request, course_id, user_access, **kwargs):
        """
        Renders a course message fragment for the specified course.
        """
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, 'load', course_key)

        # Get time until the start date, if already started, or no start date, value will be zero or negative
        now = datetime.now(UTC())
        already_started = course.start and now > course.start
        days_until_start_string = "started" if already_started else format_timedelta(course.start - now, locale=to_locale(get_language()))
        course_start_data = {
            'course_start_date': format_date(course.start, locale=to_locale(get_language())),
            'already_started': already_started,
            'days_until_start_string': days_until_start_string
        }

        # Register the course home messages to be loaded on the page
        self.register_course_home_messages(request, course, user_access, course_start_data)

        # Grab the relevant messages
        course_home_messages = list(CourseHomeMessages.user_messages(request))

        # Return None if user is enrolled and course has begun
        if user_access['is_enrolled'] and already_started:
            return None

        # Grab the logo
        image_src = "course_experience/images/home_message_author.png"

        context = {
            'course_home_messages': course_home_messages,
            'image_src': image_src,
        }

        html = render_to_string('course_experience/course-messages-fragment.html', context)
        return Fragment(html)

    @staticmethod
    def register_course_home_messages(request, course, user_access, course_start_data):
        """
        Register messages to be shown in the course home content page.
        """
        if user_access['is_anonymous']:
            CourseHomeMessages.register_info_message(
                request,
                Text(_(
                    " {sign_in_link} or {register_link} and then enroll in this course."
                )).format(
                    sign_in_link=HTML("<a href='/login?next={current_url}'>{sign_in_label}</a>").format(
                        sign_in_label=_("Sign in"),
                        current_url=urlquote_plus(request.path),
                    ),
                    register_link=HTML("<a href='/register?next={current_url}'>{register_label}</a>").format(
                        register_label=_("register"),
                        current_url=urlquote_plus(request.path),
                    )
                ),
                title='You must be enrolled in the course to see course content.'
            )
        if not user_access['is_anonymous'] and not user_access['is_staff'] and not user_access['is_enrolled']:
            CourseHomeMessages.register_info_message(
                request,
                Text(_(
                    "{open_enroll_link} Enroll now{close_enroll_link} to access the full course."
                )).format(
                    open_enroll_link='',
                    close_enroll_link=''
                ),
                title=Text('Welcome to {course_display_name}').format(
                    course_display_name=course.display_name
                )
            )
        if user_access['is_enrolled'] and not course_start_data['already_started']:
            CourseHomeMessages.register_info_message(
                request,
                Text(_(
                    "{add_reminder_open_tag}Don't forget to add a calendar reminder!{add_reminder_close_tag}."
                )).format(
                    add_reminder_open_tag='',
                    add_reminder_close_tag=''
                ),
                title=Text("Course starts in {days_until_start_string} on {course_start_date}.").format(
                    days_until_start_string=course_start_data['days_until_start_string'],
                    course_start_date=course_start_data['course_start_date']
                )
            )
