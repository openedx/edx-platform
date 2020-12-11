"""
Utility functions for event tracking processing.
"""

from django.core.exceptions import MultipleObjectsReturned

from . import exceptions


def get_site_config_for_event(event_props):
    """
    Try multiple strategies to find a SiteConfiguration object to use
    for evaluating and processing an event.

    Return a SiteConfiguration object if found; otherwise, None.
    """
    from openedx.core.djangoapps.appsembler.sites import utils
    from openedx.core.djangoapps.site_configuration import helpers
    from organizations import models

    # try first via request obj in thread
    site_configuration = helpers.get_current_site_configuration()
    if not site_configuration:
        try:
            if 'org' in event_props:
                org_name = event_props['org']
                org = models.Organization.objects.get(short_name=org_name)
            # try by OrganizationCourse relationship if event has a course_id property
            elif 'course_id' in event_props:
                course_id = event_props['course_id']
                # allow to fail if more than one Organization to avoid sharing data
                orgcourse = models.OrganizationCourse.objects.get(course_id=args)
                org = orgcourse.organization
            else:
                raise exceptions.EventProcessingError(
                    "There isn't and org or course_id attribute set in the "
                    "segment event, so we couldn't determine the site."
                )
            site = utils.get_site_by_organization(org)
            site_configuration = site.configuration
        except (
            AttributeError,
            TypeError,
            MultipleObjectsReturned,
            models.Organization.DoesNotExist,
            models.OrganizationCourse.DoesNotExist
        ) as e:
            raise exceptions.EventProcessingError(e)
    return site_configuration
