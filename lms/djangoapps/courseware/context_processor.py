"""
Any template context processors needed for the LMS
"""

import re
from django.conf import settings
from django.template.loader import render_to_string as django_render_to_string

_cached_renderings_by_course_id = {}

_notifications_namespace_regex = re.compile(r'/courses/{}/*'.format(settings.COURSE_ID_PATTERN))


def notifications_context_processor(request):
    """
    Adds - if feature is enabled - any related context information needed to render
    the notifications widget
    """

    if not settings.FEATURES.get('ENABLE_NOTIFICATIONS', False):
        return {}

    ss = _notifications_namespace_regex.search(request.path)
    if not ss:
        return {}

    course_id = ss.groupdict().get('course_id', None)
    if not course_id:
        course_id = ""

    # put the import here in case edx_notifications has not been installed in the virtual env
    from edx_notifications.server.web.utils import get_notifications_widget_context

    if course_id not in _cached_renderings_by_course_id:
        # call to the helper method to build up all the context we need
        # to render the "notification_widget" that is embedded in our
        # test page
        context_dict = get_notifications_widget_context({
            'STATIC_URL': '/static/',
            'global_variables': {
                'hide_link_is_visible': False,
                'always_show_dates_on_unread': True,
            },
            'refresh_watcher': {
                'name': 'short-poll',
                'args': {
                    'poll_period_secs': getattr(settings, 'NOTIFICATIONS_SHORT_POLL_REFRESH_RATE', 30)
                },
            },
            'namespace': course_id if course_id else None,
        })

        _cached_renderings_by_course_id[course_id] = {
            'notifications_header_html': django_render_to_string('django/notifications_widget_header.html', context_dict),
            'notifications_body_html': django_render_to_string('django/notifications_widget_body.html', context_dict)
        }

    return {
        'notifications_header_html': _cached_renderings_by_course_id[course_id]['notifications_header_html'],
        'notifications_body_html': _cached_renderings_by_course_id[course_id]['notifications_body_html'],
    }
