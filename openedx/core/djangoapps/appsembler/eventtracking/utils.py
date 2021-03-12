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
from django.core.exceptions import MultipleObjectsReturned

from openedx.core.djangoapps.site_configuration.helpers import (
    get_current_site_configuration
)

from openedx.core.djangoapps.appsembler.eventtracking.exceptions import (
    EventProcessingError
)


def get_site_config_for_event(event_props):
    """
    Try multiple strategies to find a SiteConfiguration object to use
    for evaluating and processing an event.

    Return a SiteConfiguration object if found; otherwise, None.

    django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet

    We get the site matching the org direcly from the organization object
    instead of calling 'appsembler.sites.utils.get_site_by_organization'. The
    problem is that importing 'appsembler.sites.utils' in this module at the
    module level causes the following exception:

        `django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet`
    """

    # try first via request obj in thread
    from organizations.models import Organization

    site_configuration = get_current_site_configuration()
    if not site_configuration:
        try:
            if 'org' in event_props:
                org_name = event_props['org']
                org = Organization.objects.get(short_name=org_name)
            # try by OrganizationCourse relationship if event has a course_id property
            elif 'course_id' in event_props:
                course_id = event_props['course_id']
                # allow to fail if more than one Organization to avoid sharing data
                org = Organization.objects.get(
                    organizationcourse__course_id=str(course_id))
            else:
                raise EventProcessingError(
                    "There isn't and org or course_id attribute set in the "
                    "segment event, so we couldn't determine the site."
                )
            # Same logic as in 'appsembler.sites.utils.get_site_by_organization'
            # See function docstring for additional comments
            assert org.sites.count() == 1, 'Should have one and only one site.'
            site = org.sites.all()[0]
            site_configuration = site.configuration
        except (
            AttributeError,
            TypeError,
            MultipleObjectsReturned,
            Organization.DoesNotExist
        ) as e:
            raise EventProcessingError(e)
    return site_configuration
