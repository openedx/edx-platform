"""
Utility functions for event tracking processing.

Used outside of this app by 'common/djangoapps/track/shim.py'.
See the `DefaultMultipleSegmentClient` class



TODO: Refactor to remove this module

Why? The `utils` module is and anti-pattern. It encourages coincidental cohesion
(loosely, non-specific grab-back bucketing
of functionality). Yes, naming matters.

Where? appsembler.eventracking.sites is a likely candidate as the purpose of the
`get_site_config_for_event` is specific to sites.
"""

import logging

from django.core.exceptions import MultipleObjectsReturned

from openedx.core.djangoapps.site_configuration.helpers import (
    get_current_site_configuration
)

from openedx.core.djangoapps.appsembler.eventtracking.exceptions import (
    EventProcessingError
)


log = logging.getLogger(__name__)


def get_site_config_for_event(event_props):
    """
    Try multiple strategies to find a SiteConfiguration object to use
    for evaluating and processing an event.

    Return a SiteConfiguration object if found; otherwise, None.

    django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet
    """

    # try first via request obj in thread
    from organizations.models import Organization
    from tahoe_sites.api import get_site_by_organization

    site_configuration = get_current_site_configuration()
    if not site_configuration:
        try:
            if 'org' in event_props:
                org_name = event_props['org']
                org = Organization.objects.get(short_name=org_name)
            # try by OrganizationCourse relationship if event has a course_id property
            elif 'course_id' in event_props or 'course_key' in event_props:
                if 'course_id' in event_props:
                    course_id = event_props['course_id']
                else:
                    course_id = event_props['course_key']
                # allow to fail if more than one Organization to avoid sharing data
                org = Organization.objects.get(
                    organizationcourse__course_id=str(course_id))
            else:
                raise EventProcessingError(
                    "There isn't and org, course_key or course_id attribute set in the "
                    "segment event, so we couldn't determine the site."
                )
            site_configuration = get_site_by_organization(org).configuration
        except (
            AttributeError,
            TypeError,
            MultipleObjectsReturned,
            Organization.DoesNotExist
        ) as e:
            log.exception('get_site_config_for_event: Cannot get site config for event. props=`%s`', repr(event_props))
            raise EventProcessingError(e)
    return site_configuration


def get_user_id_from_event(event_props):
    """
    Get a user id from event properties.

    For events emitted without a request. This would generally be an event emitted
    by a Celery worker, e.g., `edx.bi.completion.*` or `.grade_calculated` events.
    """

    user_id = None
    if event_props.get('user_id'):
        user_id = event_props['user_id']
    else:
        event = event_props.get('event', {})
        context = event_props.get('context', {})
        event_context = event.get('context', {})
        if context.get('user_id'):
            user_id = context.get('user_id')
            return user_id
        if event.get('user_id'):
            user_id = event.get('user_id')
            return user_id
        if event_context.get('user_id'):
            user_id = event_context.get('user_id')
            return user_id
    return user_id
