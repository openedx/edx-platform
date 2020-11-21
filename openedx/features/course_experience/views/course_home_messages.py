"""
View logic for handling course messages.
"""


from datetime import datetime

from babel.dates import format_date, format_timedelta
from django.contrib import auth
from django.template.loader import render_to_string
from django.utils.http import urlquote_plus
from django.utils.translation import get_language, to_locale
from django.utils.translation import ugettext as _
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from web_fragments.fragment import Fragment

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware.courses import get_course_date_blocks, get_course_with_access
from lms.djangoapps.course_goals.api import (
    get_course_goal,
    get_course_goal_options,
    get_goal_api_url,
    has_course_goal_permission,
    valid_course_goals_ordered
)
from lms.djangoapps.course_goals.models import GOAL_KEY_CHOICES
from lms.djangoapps.courseware.access_utils import check_public_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.course_experience import CourseHomeMessages
from common.djangoapps.student.models import CourseEnrollment
from xmodule.course_module import COURSE_VISIBILITY_PUBLIC


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
        days_until_start_string = "started" if already_started else format_timedelta(
            course.start - now, locale=to_locale(get_language())
        )
        course_start_data = {
            'course_start_date': format_date(course.start, locale=to_locale(get_language())),
            'already_started': already_started,
            'days_until_start_string': days_until_start_string
        }

        # Register the course home messages to be loaded on the page
        _register_course_home_messages(request, course, user_access, course_start_data)

        # Register course date alerts
        for course_date_block in get_course_date_blocks(course, request.user, request):
            course_date_block.register_alerts(request, course)

        # Register a course goal message, if appropriate
        # Only show the set course goal message for enrolled, unverified
        # users that have not yet set a goal in a course that allows for
        # verified statuses.
        user_goal = get_course_goal(auth.get_user(request), course_key)
        is_already_verified = CourseEnrollment.is_enrolled_as_verified(request.user, course_key)
        if has_course_goal_permission(request, course_id, user_access) and not is_already_verified and not user_goal:
            _register_course_goal_message(request, course)

        # Grab the relevant messages
        course_home_messages = list(CourseHomeMessages.user_messages(request))

        # Pass in the url used to set a course goal
        goal_api_url = get_goal_api_url(request)

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
    allow_anonymous = check_public_access(course, [COURSE_VISIBILITY_PUBLIC])

    if user_access['is_anonymous'] and not allow_anonymous:
        sign_in_or_register_text = (_(u'{sign_in_link} or {register_link} and then enroll in this course.')
                                    if not CourseMode.is_masters_only(course.id)
                                    else _(u'{sign_in_link} or {register_link}.'))
        CourseHomeMessages.register_info_message(
            request,
            Text(sign_in_or_register_text).format(
                sign_in_link=HTML(u'<a href="/login?next={current_url}">{sign_in_label}</a>').format(
                    sign_in_label=_('Sign in'),
                    current_url=urlquote_plus(request.path),
                ),
                register_link=HTML(u'<a href="/register?next={current_url}">{register_label}</a>').format(
                    register_label=_('register'),
                    current_url=urlquote_plus(request.path),
                )
            ),
            title=Text(_('You must be enrolled in the course to see course content.'))
        )
    if not user_access['is_anonymous'] and not user_access['is_staff'] and \
            not user_access['is_enrolled']:

        title = Text(_(u'Welcome to {course_display_name}')).format(
            course_display_name=course.display_name
        )

        if CourseMode.is_masters_only(course.id):
            # if a course is a Master's only course, we will not offer user ability to self-enroll
            CourseHomeMessages.register_info_message(
                request,
                Text(_('You must be enrolled in the course to see course content. '
                       'Please contact your degree administrator or edX Support if you have questions.')),
                title=title
            )
        elif not course.invitation_only:
            CourseHomeMessages.register_info_message(
                request,
                Text(_(
                    u'{open_enroll_link}Enroll now{close_enroll_link} to access the full course.'
                )).format(
                    open_enroll_link=HTML('<button class="enroll-btn btn-link">'),
                    close_enroll_link=HTML('</button>')
                ),
                title=title
            )
        else:
            CourseHomeMessages.register_info_message(
                request,
                Text(_('You must be enrolled in the course to see course content.')),
            )


def _register_course_goal_message(request, course):
    """
    Register a message to let a learner specify a course goal.
    """
    course_goal_options = get_course_goal_options()
    goal_choices_html = Text(_(
        'To start, set a course goal by selecting the option below that best describes '
        u'your learning plan. {goal_options_container}'
    )).format(
        goal_options_container=HTML('<div class="row goal-options-container">')
    )

    # Add the dismissible option for users that are unsure of their goal
    goal_choices_html += Text(
        '{initial_tag}{choice}{closing_tag}'
    ).format(
        initial_tag=HTML(
            u'<div tabindex="0" aria-label="{aria_label_choice}" class="goal-option dismissible" '
            'data-choice="{goal_key}">'
        ).format(
            goal_key=GOAL_KEY_CHOICES.unsure,
            aria_label_choice=Text(_(u"Set goal to: {choice}")).format(
                choice=course_goal_options[GOAL_KEY_CHOICES.unsure],
            ),
        ),
        choice=Text(_('{choice}')).format(
            choice=course_goal_options[GOAL_KEY_CHOICES.unsure],
        ),
        closing_tag=HTML('</div>'),
    )

    # Add the option to set a goal to earn a certificate,
    # complete the course or explore the course
    course_goals_by_commitment_level = valid_course_goals_ordered()
    for goal in course_goals_by_commitment_level:
        goal_key, goal_text = goal
        goal_choices_html += HTML(
            '{initial_tag}{goal_text}{closing_tag}'
        ).format(
            initial_tag=HTML(
                u'<button tabindex="0" aria-label="{aria_label_choice}" class="goal-option btn-outline-primary" '
                'data-choice="{goal_key}">'
            ).format(
                goal_key=goal_key,
                aria_label_choice=Text(_(u"Set goal to: {goal_text}")).format(
                    goal_text=Text(_(goal_text))
                )
            ),
            goal_text=goal_text,
            closing_tag=HTML('</button>')
        )

    CourseHomeMessages.register_info_message(
        request,
        HTML('{goal_choices_html}{closing_tag}').format(
            goal_choices_html=goal_choices_html,
            closing_tag=HTML('</div>')
        ),
        title=Text(_(u'Welcome to {course_display_name}')).format(
            course_display_name=course.display_name
        )
    )
