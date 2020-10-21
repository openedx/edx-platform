"""
All utilities for Django sites
"""
from logging import getLogger

from django.contrib.sites.models import Site

log = getLogger(__name__)


def get_site(site_id):
    """
    Get site object from site id
    Args:
        site_id (int): the id of site

    Returns:
        site: The site object otherwise None
    """
    try:
        return Site.objects.get(id=site_id)
    except Site.DoesNotExist:
        log.error('Site with id {id}, does not exists'.format(id=site_id))
