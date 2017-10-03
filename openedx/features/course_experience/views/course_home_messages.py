"""
View logic for handling course messages.
"""
import math
from datetime import datetime

from babel.dates import format_date, format_timedelta
from django.conf import settings
from django.contrib import auth
from django.template.loader import render_to_string
from django.utils.http import urlquote_plus
from pytz import UTC
from django.utils.translation import get_language, to_locale
from django.utils.translation import ugettext as _
from django.utils.translation import get_language, to_locale
from opaque_keys.edx.keys import CourseKey
from rest_framework.reverse import reverse
from web_fragments.fragment import Fragment

from course_modes.models import CourseMode
from courseware.courses import get_course_date_blocks, get_course_with_access
from lms.djangoapps.course_goals.api import get_course_goal
from lms.djangoapps.course_goals.models import GOAL_KEY_CHOICES
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.course_experience import CourseHomeMessages
from student.models import CourseEnrollment

from .. import ENABLE_COURSE_GOALS


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
        now = datetime.now(UTC)
        already_started = course.start and now > course.start
        days_until_start_string = "started" if already_started else format_timedelta(course.start - now, locale=to_locale(get_language()))
        course_start_data = {
            'course_start_date': format_date(course.start, locale=to_locale(get_language())),
            'already_started': already_started,
            'days_until_start_string': days_until_start_string
        }

        # Register the course home messages to be loaded on the page
        _register_course_home_messages(request, course, user_access, course_start_data)

        # Register course date alerts
        for course_date_block in get_course_date_blocks(course, request.user):
            course_date_block.register_alerts(request, course)

        # Register a course goal message, if appropriate
        if _should_show_course_goal_message(request, course, user_access):
            _register_course_goal_message(request, course)

        # Grab the relevant messages
        course_home_messages = list(CourseHomeMessages.user_messages(request))

        # Pass in the url used to set a course goal
        goal_api_url = reverse('course_goals_api:v0:course_goal-list', request=request)

        # Grab the logo
        image_src = 'course_experience/images/home_message_author.png'

        context = {
            'course_home_messages': course_home_messages,
            'goal_api_url': goal_api_url,
            'image_src': image_src,
            'course_id': course_id,
            'username': request.user.username,
        }

        html = render_to_string('course_experience/course-messages-fragment.html', context)
        return Fragment(html)


def _register_course_home_messages(request, course, user_access, course_start_data):
    """
    Register messages to be shown in the course home content page.
    """
    if user_access['is_anonymous']:
        CourseHomeMessages.register_info_message(
            request,
            Text(_(
                '{sign_in_link} or {register_link} and then enroll in this course.'
            )).format(
                sign_in_link=HTML('<a href="/login?next={current_url}">{sign_in_label}</a>').format(
                    sign_in_label=_('Sign in'),
                    current_url=urlquote_plus(request.path),
                ),
                register_link=HTML('<a href="/register?next={current_url}">{register_label}</a>').format(
                    register_label=_('register'),
                    current_url=urlquote_plus(request.path),
                )
            ),
            title=Text(_('You must be enrolled in the course to see course content.'))
        )
    if not user_access['is_anonymous'] and not user_access['is_staff'] and not user_access['is_enrolled']:
        CourseHomeMessages.register_info_message(
            request,
            Text(_(
                '{open_enroll_link}Enroll now{close_enroll_link} to access the full course.'
            )).format(
                open_enroll_link='',
                close_enroll_link=''
            ),
            title=Text(_('Welcome to {course_display_name}')).format(
                course_display_name=course.display_name
            )
        )


def _should_show_course_goal_message(request, course, user_access):
    """
    Returns true if the current learner should be shown a course goal message.
    """
    course_key = course.id

    # Don't show a message if course goals has not been enabled
    if not ENABLE_COURSE_GOALS.is_enabled(course_key) or not settings.FEATURES.get('ENABLE_COURSE_GOALS'):
        return False

    # Don't show a message if the user is not enrolled
    if not user_access['is_enrolled']:
        return False

    # Don't show a message if the learner has already specified a goal
    if get_course_goal(auth.get_user(request), course_key):
        return False

    # Don't show a message if the course does not have a verified mode
    if not CourseMode.has_verified_mode(CourseMode.modes_for_course_dict(unicode(course_key))):
        return False

    # Don't show a message if the learner has already verified
    if CourseEnrollment.is_enrolled_as_verified(request.user, course_key):
        return False

    return True


def _register_course_goal_message(request, course):
    """
    Register a message to let a learner specify a course goal.
    """
    goal_choices_html = Text(_(
        'To start, set a course goal by selecting the option below that best describes '
        'your learning plan. {goal_options_container}'
    )).format(
        goal_options_container=HTML('<div class="row goal-options-container">')
    )

    # Add the dismissible option for users that are unsure of their goal
    goal_choices_html += Text(
        '{initial_tag}{choice}{closing_tag}'
    ).format(
        initial_tag=HTML(
            '<div tabindex="0" aria-label="{aria_label_choice}" class="goal-option dismissible" '
            'data-choice="{goal_key}">'
        ).format(
            goal_key=GOAL_KEY_CHOICES.unsure,
            aria_label_choice=Text(_("Set goal to: {choice}")).format(
                choice=GOAL_KEY_CHOICES[GOAL_KEY_CHOICES.unsure]
            ),
        ),
        choice=Text(_('{choice}')).format(
            choice=GOAL_KEY_CHOICES[GOAL_KEY_CHOICES.unsure],
        ),
        closing_tag=HTML('</div>'),
    )

    # Add the option to set a goal to earn a certificate,
    # complete the course or explore the course
    goal_options = [
        GOAL_KEY_CHOICES.certify,
        GOAL_KEY_CHOICES.complete,
        GOAL_KEY_CHOICES.explore
    ]
    for goal_key in goal_options:
        goal_text = GOAL_KEY_CHOICES[goal_key]
        goal_choices_html += HTML(
            '{initial_tag}{goal_text}{closing_tag}'
        ).format(
            initial_tag=HTML(
                '<div tabindex="0" aria-label="{aria_label_choice}" class="goal-option {col_sel} btn" '
                'data-choice="{goal_key}">'
            ).format(
                goal_key=goal_key,
                aria_label_choice=Text(_("Set goal to: {goal_text}")).format(
                    goal_text=Text(_(goal_text))
                ),
                col_sel='col-' + str(int(math.floor(12 / len(goal_options))))
            ),
            goal_text=goal_text,
            closing_tag=HTML('</div>')
        )

    CourseHomeMessages.register_info_message(
        request,
        goal_choices_html,
        title=Text(_('Welcome to {course_display_name}')).format(
            course_display_name=course.display_name
        )
    )
