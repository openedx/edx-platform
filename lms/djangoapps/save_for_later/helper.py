"""
helper functions
"""

import logging
from datetime import datetime
from django.conf import settings
from eventtracking import tracker

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.utils import get_braze_client

log = logging.getLogger(__name__)

USER_SAVE_FOR_LATER_EMAIL_SENT = 'edx.bi.user.saveforlater.email.sent'
USER_SAVE_FOR_LATER_REMINDER_EMAIL_SENT = 'edx.bi.user.saveforlater.reminder.email.sent'


def _get_program_pacing(course_runs):
    """
        get pacing type of published course run of course for program
    """

    pacing = [course_run.get('pacing_type') if course_run.get('status') == 'published'
              else '' for course_run in course_runs][0]
    return 'Self-paced' if pacing == 'self_paced' else 'Instructor-led'


def _get_course_price(course):
    """
        Get price of a course
    """
    return CourseMode.min_course_price_for_currency(course_id=str(course.id), currency='USD')


def _get_event_properties(data):
    """
    set event properties for course and program which are required in braze email template
    """
    lms_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    event_properties = {
        'time': datetime.now().isoformat(),
        'name': data.get('braze_event'),
    }

    event_type = data.get('type')
    if event_type == 'course':
        course = data.get('course')
        price = _get_course_price(course)
        event_properties.update({
            'properties': {
                'course_image_url': '{base_url}{image_path}'.format(
                    base_url=lms_url, image_path=course.course_image_url
                ),
                'partner_image_url': data.get('org_img_url'),
                'enroll_course_url': '{base_url}/register?course_id={course_id}&enrollment_action=enroll&email_opt_in='
                                     'false&save_for_later=true'.format(base_url=lms_url, course_id=course.id),
                'view_course_url': data.get('marketing_url') + '?save_for_later=true' if data.get(
                    'marketing_url') else '#',
                'display_name': course.display_name,
                'short_description': course.short_description,
                'weeks_to_complete': data.get('weeks_to_complete'),
                'min_effort': data.get('min_effort'),
                'max_effort': data.get('max_effort'),
                'pacing_type': 'Self-paced' if course.self_paced else 'Instructor-led',
                'type': event_type,
                'price': 'Free' if price == 0 else f'${price} USD',
            }
        })

    if event_type == 'program':
        program = data.get('program')
        price = int(program.get('price_ranges')[0].get('total'))
        event_properties.update({
            'properties': {
                'program_image_url': program.get('card_image_url'),
                'partner_image_url': program.get('authoring_organizations')[0].get('logo_image_url') if program.get(
                    'authoring_organizations') else None,
                'view_program_url': program.get('marketing_url') + '?save_for_later=true' if program.get(
                    'marketing_url') else '#',
                'title': program.get('title'),
                'education_level': program.get('type'),
                'total_courses': len(program.get('courses')) if program.get('courses') else 0,
                'weeks_to_complete': program.get('weeks_to_complete'),
                'min_effort': program.get('min_hours_effort_per_week'),
                'max_effort': program.get('max_hours_effort_per_week'),
                'pacing_type': _get_program_pacing(program.get('courses')[0].get('course_runs')),
                'price': f'${price} USD',
                'registered': bool(program.get('type') in ['MicroMasters', 'MicroBachelors']),
                'type': event_type,
            }
        })
    return event_properties


def send_email(email, data):
    """
    Send email through Braze
    """
    event_properties = _get_event_properties(data)
    braze_client = get_braze_client()

    if not braze_client:
        return False

    try:
        attributes = None
        external_id = braze_client.get_braze_external_id(email)
        if external_id:
            event_properties.update({'external_id': external_id})
        else:
            braze_client.create_braze_alias(emails=[email], alias_label='save_for_later')
            user_alias = {
                'alias_label': 'save_for_later',
                'alias_name': email,
            }
            event_properties.update({'user_alias': user_alias})
            attributes = [{
                'user_alias': user_alias,
                'pref-lang': data.get('pref-lang', 'en')
            }]

        braze_client.track_user(events=[event_properties], attributes=attributes)

        event_type = data.get('type')
        event_data = {
            'user_id': data.get('user_id'),
            'category': 'save-for-later',
            'type': event_type,
            'send_to_self': data.get('send_to_self'),
        }
        if event_type == 'program':
            program = data.get('program')
            event_data.update({'program_uuid': program.get('uuid')})
        elif event_type == 'course':
            course = data.get('course')
            event_data.update({'course_key': str(course.id)})

        tracker.emit(
            USER_SAVE_FOR_LATER_REMINDER_EMAIL_SENT if data.get('reminder') else USER_SAVE_FOR_LATER_EMAIL_SENT,
            event_data
        )
    except Exception:  # pylint: disable=broad-except
        log.warning('Unable to send save for later email ', exc_info=True)
        return False
    else:
        return True
