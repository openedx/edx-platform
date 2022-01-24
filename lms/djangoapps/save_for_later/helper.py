"""
helper functions
"""

import logging
from datetime import datetime
from django.conf import settings
from braze.client import BrazeClient
from eventtracking import tracker

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)

USER_SENT_EMAIL_SAVE_FOR_LATER = 'edx.bi.user.saveforlater.email.sent'


def _get_event_properties(data):
    """
    set event properties for course and program which are required in braze email template
    """
    lms_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    event_properties = {
        'time': datetime.now().isoformat(),
        'name': 'user.send.save.for.later.email',
    }

    if data.get('type') == 'course':
        course = data.get('course')
        org_img_url = data.get('org_img_url')
        marketing_url = data.get('marketing_url')
        event_properties.update({
            'properties': {
                'course_image_url': '{base_url}{image_path}'.format(
                    base_url=lms_url, image_path=course.course_image_url
                ),
                'partner_image_url': org_img_url,
                'enroll_course_url': '{base_url}/register?course_id={course_id}&enrollment_action=enroll&email_opt_in='
                                     'false&save_for_later=true'.format(base_url=lms_url, course_id=course.id),
                'view_course_url': marketing_url + '?save_for_later=true' if marketing_url else '#',
                'display_name': course.display_name,
                'short_description': course.short_description,
                'type': 'course',
            }
        })

    if data.get('type') == 'program':
        program = data.get('program')
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
                'type': 'program',
            }
        })
    return event_properties


def send_email(request, email, data):
    """
    Send email through Braze
    """
    event_properties = _get_event_properties(data)
    braze_client = BrazeClient(
        api_key=settings.EDX_BRAZE_API_KEY,
        api_url=settings.EDX_BRAZE_API_SERVER,
        app_id='',
    )

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
                'pref-lang': request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, 'en')
            }]

        braze_client.track_user(events=[event_properties], attributes=attributes)
        tracker.emit(
            USER_SENT_EMAIL_SAVE_FOR_LATER,
            {
                'user_id': request.user.id,
                'category': 'save-for-later',
                'type': event_properties.get('type'),
                'send_to_self': bool(not request.user.is_anonymous and request.user.email == email),
            }
        )
    except Exception:  # pylint: disable=broad-except
        log.warning('Unable to send save for later email ', exc_info=True)
        return False
    else:
        return True
